// ================================================================
// NextGen Hospital Management System
// Patient Management Microservice
// Production-Ready .NET 8 Implementation - ZFP-ADAPTED
// ================================================================

using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Security.Claims;
using System.Text;
using Serilog;
using FluentValidation;
using MediatR;
using Polly;
using StackExchange.Redis;
using System.Text.Json; // Added for AI-API DTO parsing
using System.Net.Http.Json; // Added for AI-API Client

// ================================================================
// Program.cs - Application Entry Point
// ================================================================

var builder = WebApplication.CreateBuilder(args);

// Logging with Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .WriteTo.Console()
    .WriteTo.Seq(builder.Configuration["Seq:ServerUrl"]!)
    .WriteTo.File("logs/patient-service-.txt", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Database
builder.Services.AddDbContext<PatientDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("PatientDb")!,
        npgsql => npgsql.EnableRetryOnFailure(5)));

// Redis Cache
builder.Services.AddSingleton<IConnectionMultiplexer>(
    ConnectionMultiplexer.Connect(builder.Configuration["Redis:ConnectionString"]!));
builder.Services.AddScoped<ICacheService, RedisCacheService>();

// Authentication
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = builder.Configuration["Auth:Authority"];
        options.Audience = builder.Configuration["Auth:Audience"];
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ClockSkew = TimeSpan.Zero
        };
    });

// Authorization Policies
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("PatientRead", policy =>
        policy.RequireClaim("permissions", "patient:read"));
    options.AddPolicy("PatientWrite", policy =>
        policy.RequireClaim("permissions", "patient:write"));
    options.AddPolicy("PatientDelete", policy =>
        policy.RequireClaim("permissions", "patient:delete"));
});

// MediatR for CQRS
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(Program).Assembly));

// FluentValidation
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

// Health Checks
builder.Services.AddHealthChecks()
    .AddNpgSql(builder.Configuration.GetConnectionString("PatientDb")!)
    .AddRedis(builder.Configuration["Redis:ConnectionString"]!);

// Message Bus (RabbitMQ)
builder.Services.AddMassTransit(config =>
{
    config.UsingRabbitMq((context, cfg) =>
    {
        cfg.Host(builder.Configuration["RabbitMQ:Host"], h =>
        {
            h.Username(builder.Configuration["RabbitMQ:Username"]!);
            h.Password(builder.Configuration["RabbitMQ:Password"]!);
        });
    });
});

// Resilience Policies
builder.Services.AddHttpClient<IExternalService, ExternalService>()
    .AddTransientHttpErrorPolicy(policy =>
        policy.WaitAndRetryAsync(3, retryAttempt =>
            TimeSpan.FromSeconds(Math.Pow(2, retryAttempt))))
    .AddTransientHttpErrorPolicy(policy =>
        policy.CircuitBreakerAsync(5, TimeSpan.FromSeconds(30)));

// API Documentation
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "Patient Service API", Version = "v1" });
    c.AddSecurityDefinition("Bearer", new()
    {
        Description = "JWT Authorization header using the Bearer scheme",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });
});

builder.Services.AddControllers();
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>()!)
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials();
    });
});

// Services (ZFP AI-API INTEGRATION - LOCAL SERVICES REPLACED BY ADAPTERS)
builder.Services.AddScoped<IPatientService, PatientService>();
// Removed: builder.Services.AddScoped<IEncryptionService, EncryptionService>();
// Removed: builder.Services.AddScoped<IAuditService, AuditService>();

// CRITICAL: ADD ZFP AI-API CLIENT AND ITS DEPENDENCIES
builder.Services.AddHttpClient<IAiApiNegotiator, AiApiNegotiator>(client =>
{
    // Fetches http://ai-api-service.hospital-system.svc.cluster.local:8088/ from ConfigMap
    client.BaseAddress = new Uri(builder.Configuration["AiApi:BaseUrl"]!);
    client.Timeout = TimeSpan.FromSeconds(5); // Non-negotiable ZFP execution time limit
});

// NEW: Adapters now use the remote AI-API for execution
builder.Services.AddScoped<IEncryptionService, AiApiEncryptionAdapter>(); 
builder.Services.AddScoped<IAuditService, AiApiAuditAdapter>(); 

var app = builder.Build();

// Middleware Pipeline
app.UseSerilogRequestLogging();
app.UseHttpsRedirection();
app.UseCors();
app.UseAuthentication();
app.UseAuthorization();

// Health Checks
app.MapHealthChecks("/health");
app.MapHealthChecks("/ready");

// Swagger
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapControllers();

// Database Migration on Startup
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<PatientDbContext>();
    await db.Database.MigrateAsync();
}

Log.Information("Patient Service starting...");
app.Run();

// ================================================================
// Domain Models
// ================================================================

public class Patient
{
    public Guid PatientId { get; set; }
    public string MRN { get; set; } = string.Empty; // Medical Record Number
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public DateTime DateOfBirth { get; set; }
    public char Sex { get; set; } // M, F, O, U
    
    // Encrypted fields
    public byte[]? SSNEncrypted { get; set; }
    public byte[]? InsurancePolicyNumberEncrypted { get; set; }
    
    // Contact
    public string? Phone { get; set; }
    public string? Email { get; set; }
    public Address? Address { get; set; }
    
    // Insurance
    public string? InsuranceProvider { get; set; }
    
    // Metadata
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public Guid CreatedBy { get; set; }
    public bool IsDeleted { get; set; }
    
    // Navigation
    public List<Encounter> Encounters { get; set; } = new();
    public List<Allergy> Allergies { get; set; } = new();
    public List<Medication> Medications { get; set; } = new();
}

public class Address
{
    public string Line1 { get; set; } = string.Empty;
    public string? Line2 { get; set; }
    public string City { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public string ZipCode { get; set; } = string.Empty;
    public string Country { get; set; } = "USA";
}

public class Encounter
{
    public Guid EncounterId { get; set; }
    public Guid PatientId { get; set; }
    public Patient Patient { get; set; } = null!;
    
    public EncounterType Type { get; set; }
    public string? ChiefComplaint { get; set; }
    
    public DateTime AdmissionTime { get; set; }
    public DateTime? DischargeTime { get; set; }
    
    public Guid? DepartmentId { get; set; }
    public string? RoomNumber { get; set; }
    public string? BedNumber { get; set; }
    
    public List<string> AdmittingDiagnosisCodes { get; set; } = new();
    public List<string> DischargeDiagnosisCodes { get; set; } = new();
    
    public Guid? AttendingPhysicianId { get; set; }
    public EncounterStatus Status { get; set; }
    
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public enum EncounterType
{
    Inpatient,
    Outpatient,
    Emergency,
    Observation
}

public enum EncounterStatus
{
    Active,
    Discharged,
    Transferred,
    Cancelled
}

public class Allergy
{
    public Guid AllergyId { get; set; }
    public Guid PatientId { get; set; }
    public string Allergen { get; set; } = string.Empty;
    public AllergySeverity Severity { get; set; }
    public string? Reaction { get; set; }
    public DateTime OnsetDate { get; set; }
    public bool IsActive { get; set; } = true;
}

public enum AllergySeverity
{
    Mild,
    Moderate,
    Severe,
    LifeThreatening
}

public class Medication
{
    public Guid MedicationId { get; set; }
    public Guid PatientId { get; set; }
    public string MedicationName { get; set; } = string.Empty;
    public string RxNormCode { get; set; } = string.Empty;
    public string Dosage { get; set; } = string.Empty;
    public string Frequency { get; set; } = string.Empty;
    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }
    public Guid PrescribedBy { get; set; }
    public bool IsActive { get; set; } = true;
}

// ================================================================
// Database Context
// ================================================================

public class PatientDbContext : DbContext
{
    public PatientDbContext(DbContextOptions<PatientDbContext> options) : base(options) { }

    public DbSet<Patient> Patients { get; set; } = null!;
    public DbSet<Encounter> Encounters { get; set; } = null!;
    public DbSet<Allergy> Allergies { get; set; } = null!;
    public DbSet<Medication> Medications { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Patient Configuration
        modelBuilder.Entity<Patient>(entity =>
        {
            entity.HasKey(e => e.PatientId);
            entity.HasIndex(e => e.MRN).IsUnique();
            entity.HasIndex(e => e.DateOfBirth);
            entity.HasIndex(e => new { e.LastName, e.FirstName });
            
            entity.OwnsOne(e => e.Address);
            
            entity.Property(e => e.MRN).HasMaxLength(50).IsRequired();
            entity.Property(e => e.FirstName).HasMaxLength(100).IsRequired();
            entity.Property(e => e.LastName).HasMaxLength(100).IsRequired();
            entity.Property(e => e.Email).HasMaxLength(255);
            
            // Soft delete filter
            entity.HasQueryFilter(e => !e.IsDeleted);
        });

        // Encounter Configuration
        modelBuilder.Entity<Encounter>(entity =>
        {
            entity.HasKey(e => e.EncounterId);
            entity.HasIndex(e => e.PatientId);
            entity.HasIndex(e => e.AdmissionTime);
            entity.HasIndex(e => e.Status).HasFilter("\"Status\" = 'Active'");
            
            entity.HasOne(e => e.Patient)
                  .WithMany(p => p.Encounters)
                  .HasForeignKey(e => e.PatientId);
        });

        // Allergy Configuration
        modelBuilder.Entity<Allergy>(entity =>
        {
            entity.HasKey(e => e.AllergyId);
            entity.HasIndex(e => new { e.PatientId, e.IsActive });
        });

        // Medication Configuration
        modelBuilder.Entity<Medication>(entity =>
        {
            entity.HasKey(e => e.MedicationId);
            entity.HasIndex(e => new { e.PatientId, e.IsActive });
            entity.HasIndex(e => e.RxNormCode);
        });
    }
}

// ================================================================
// DTOs (Data Transfer Objects)
// ================================================================

public record CreatePatientRequest(
    string FirstName,
    string LastName,
    DateTime DateOfBirth,
    char Sex,
    string? SSN,
    string? Phone,
    string? Email,
    AddressDto? Address,
    string? InsuranceProvider,
    string? InsurancePolicyNumber
);

public record AddressDto(
    string Line1,
    string? Line2,
    string City,
    string State,
    string ZipCode
);

public record PatientResponse(
    Guid PatientId,
    string MRN,
    string FirstName,
    string LastName,
    DateTime DateOfBirth,
    char Sex,
    string? Phone,
    string? Email,
    AddressDto? Address,
    string? InsuranceProvider,
    DateTime CreatedAt,
    DateTime UpdatedAt
);

public record SearchPatientRequest(
    string? Query,
    DateTime? DateOfBirthFrom,
    DateTime? DateOfBirthTo,
    int Page = 1,
    int PageSize = 20
);

public record PagedResult<T>(
    List<T> Items,
    int TotalCount,
    int Page,
    int PageSize,
    int TotalPages
);

// ================================================================
// CQRS Commands & Queries
// ================================================================

public record CreatePatientCommand(CreatePatientRequest Request) : IRequest<Result<PatientResponse>>;

public class CreatePatientCommandHandler : IRequestHandler<CreatePatientCommand, Result<PatientResponse>>
{
    private readonly PatientDbContext _context;
    private readonly IEncryptionService _encryption;
    private readonly IAuditService _audit;
    private readonly IPublishEndpoint _publisher;
    private readonly ILogger<CreatePatientCommandHandler> _logger;

    public CreatePatientCommandHandler(
        PatientDbContext context,
        IEncryptionService encryption,
        IAuditService audit,
        IPublishEndpoint publisher,
        ILogger<CreatePatientCommandHandler> logger)
    {
        _context = context;
        _encryption = encryption;
        _audit = audit;
        _publisher = publisher;
        _logger = logger;
    }

    public async Task<Result<PatientResponse>> Handle(CreatePatientCommand command, CancellationToken cancellationToken)
    {
        var req = command.Request;
        
        // Generate MRN
        var mrn = await GenerateMRN();
        
        // Encrypt sensitive data (FORCED THROUGH AI-API ADAPTER)
        byte[]? ssnEncrypted = !string.IsNullOrEmpty(req.SSN) 
            ? await _encryption.EncryptAsync(req.SSN) 
            : null;
        
        byte[]? insuranceEncrypted = !string.IsNullOrEmpty(req.InsurancePolicyNumber)
            ? await _encryption.EncryptAsync(req.InsurancePolicyNumber) 
            : null;

        var patient = new Patient
        {
            PatientId = Guid.NewGuid(),
            MRN = mrn,
            FirstName = req.FirstName,
            LastName = req.LastName,
            DateOfBirth = req.DateOfBirth,
            Sex = req.Sex,
            SSNEncrypted = ssnEncrypted,
            Phone = req.Phone,
            Email = req.Email,
            Address = req.Address != null ? new Address
            {
                Line1 = req.Address.Line1,
                Line2 = req.Address.Line2,
                City = req.Address.City,
                State = req.Address.State,
                ZipCode = req.Address.ZipCode,
                Country = "USA" // Defaulted in the Domain Model
            } : null,
            InsuranceProvider = req.InsuranceProvider,
            InsurancePolicyNumberEncrypted = insuranceEncrypted,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow,
            CreatedBy = Guid.Empty // Placeholder - Should be from claims
        };

        _context.Patients.Add(patient);
        await _context.SaveChangesAsync(cancellationToken);

        // Audit (FORCED THROUGH AI-API ADAPTER)
        await _audit.LogAsync("PatientCreated", patient.PatientId, patient);

        // Publish event
        await _publisher.Publish(new PatientCreatedEvent
        {
            PatientId = patient.PatientId,
            MRN = patient.MRN,
            FullName = $"{patient.FirstName} {patient.LastName}",
            DateOfBirth = patient.DateOfBirth,
            Timestamp = DateTime.UtcNow
        }, cancellationToken);

        _logger.LogInformation("Patient created: {PatientId} - {MRN}", patient.PatientId, patient.MRN);

        return Result<PatientResponse>.Success(MapToResponse(patient));
    }

    private async Task<string> GenerateMRN()
    {
        // Generate unique MRN: Format MRN-YYYYMMDD-XXXX
        var date = DateTime.UtcNow.ToString("yyyyMMdd");
        var sequence = await _context.Patients.CountAsync() + 1;
        return $"MRN-{date}-{sequence:D6}";
    }

    private PatientResponse MapToResponse(Patient patient) => new(
        patient.PatientId,
        patient.MRN,
        patient.FirstName,
        patient.LastName,
        patient.DateOfBirth,
        patient.Sex,
        patient.Phone,
        patient.Email,
        patient.Address != null ? new AddressDto(
            patient.Address.Line1,
            patient.Address.Line2,
            patient.Address.City,
            patient.Address.State,
            patient.Address.ZipCode
        ) : null,
        patient.InsuranceProvider,
        patient.CreatedAt,
        patient.UpdatedAt
    );
}

public record GetPatientQuery(Guid PatientId) : IRequest<Result<PatientResponse>>;

public class GetPatientQueryHandler : IRequestHandler<GetPatientQuery, Result<PatientResponse>>
{
    private readonly PatientDbContext _context;
    private readonly ICacheService _cache;
    private readonly IAuditService _audit;

    public GetPatientQueryHandler(
        PatientDbContext context, 
        ICacheService cache,
        IAuditService audit)
    {
        _context = context;
        _cache = cache;
        _audit = audit;
    }

    public async Task<Result<PatientResponse>> Handle(GetPatientQuery query, CancellationToken cancellationToken)
    {
        // Try cache first
        var cacheKey = $"patient:{query.PatientId}";
        var cached = await _cache.GetAsync<PatientResponse>(cacheKey);
        if (cached != null) return Result<PatientResponse>.Success(cached);

        // Query database
        var patient = await _context.Patients
            .Include(p => p.Address)
            .FirstOrDefaultAsync(p => p.PatientId == query.PatientId, cancellationToken);

        if (patient == null)
            return Result<PatientResponse>.Failure("Patient not found");

        var response = new PatientResponse(
            patient.PatientId,
            patient.MRN,
            patient.FirstName,
            patient.LastName,
            patient.DateOfBirth,
            patient.Sex,
            patient.Phone,
            patient.Email,
            patient.Address != null ? new AddressDto(
                patient.Address.Line1,
                patient.Address.Line2,
                patient.Address.City,
                patient.Address.State,
                patient.Address.ZipCode
            ) : null,
            patient.InsuranceProvider,
            patient.CreatedAt,
            patient.UpdatedAt
        );

        // Cache for 5 minutes
        await _cache.SetAsync(cacheKey, response, TimeSpan.FromMinutes(5));

        // Audit access
        await _audit.LogAsync("PatientAccessed", patient.PatientId);

        return Result<PatientResponse>.Success(response);
    }
}

public record SearchPatientsQuery(SearchPatientRequest Request) : IRequest<Result<PagedResult<PatientResponse>>>;

public class SearchPatientsQueryHandler : IRequestHandler<SearchPatientsQuery, Result<PagedResult<PatientResponse>>>
{
    private readonly PatientDbContext _context;

    public SearchPatientsQueryHandler(PatientDbContext context)
    {
        _context = context;
    }

    public async Task<Result<PagedResult<PatientResponse>>> Handle(
        SearchPatientsQuery query, 
        CancellationToken cancellationToken)
    {
        var req = query.Request;
        var queryable = _context.Patients.AsQueryable();

        // Full-text search
        if (!string.IsNullOrWhiteSpace(req.Query))
        {
            // Note: This needs to be configured for PostgreSQL's full-text search
            // The EF.Functions.ILike is a simple substitute for ILike in the absence of a proper FTS index utility here.
            queryable = queryable.Where(p =>
                EF.Functions.ILike(p.FirstName, $"%{req.Query}%") ||
                EF.Functions.ILike(p.LastName, $"%{req.Query}%") ||
                EF.Functions.ILike(p.MRN, $"%{req.Query}%"));
        }

        // Date of birth filter
        if (req.DateOfBirthFrom.HasValue)
            queryable = queryable.Where(p => p.DateOfBirth >= req.DateOfBirthFrom.Value);
        
        if (req.DateOfBirthTo.HasValue)
            queryable = queryable.Where(p => p.DateOfBirth <= req.DateOfBirthTo.Value);

        var totalCount = await queryable.CountAsync(cancellationToken);
        
        var patients = await queryable
            .OrderBy(p => p.LastName).ThenBy(p => p.FirstName)
            .Skip((req.Page - 1) * req.PageSize)
            .Take(req.PageSize)
            .Select(p => new PatientResponse(
                p.PatientId,
                p.MRN,
                p.FirstName,
                p.LastName,
                p.DateOfBirth,
                p.Sex,
                p.Phone,
                p.Email,
                p.Address != null ? new AddressDto(
                    p.Address.Line1,
                    p.Address.Line2,
                    p.Address.City,
                    p.Address.State,
                    p.Address.ZipCode
                ) : null,
                p.InsuranceProvider,
                p.CreatedAt,
                p.UpdatedAt
            ))
            .ToListAsync(cancellationToken);

        var result = new PagedResult<PatientResponse>(
            patients,
            totalCount,
            req.Page,
            req.PageSize,
            (int)Math.Ceiling(totalCount / (double)req.PageSize)
        );

        return Result<PagedResult<PatientResponse>>.Success(result);
    }
}

// ================================================================
// API Controllers
// ================================================================

[ApiController]
[Route("api/v1/patients")]
[Authorize]
public class PatientsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<PatientsController> _logger;

    public PatientsController(IMediator mediator, ILogger<PatientsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpPost]
    [Authorize(Policy = "PatientWrite")]
    [ProducesResponseType(typeof(PatientResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> CreatePatient([FromBody] CreatePatientRequest request)
    {
        var result = await _mediator.Send(new CreatePatientCommand(request));
        
        if (!result.IsSuccess)
            return BadRequest(result.Error);

        return CreatedAtAction(
            nameof(GetPatient), 
            new { id = result.Data!.PatientId }, 
            result.Data);
    }

    [HttpGet("{id:guid}")]
    [Authorize(Policy = "PatientRead")]
    [ProducesResponseType(typeof(PatientResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetPatient(Guid id)
    {
        var result = await _mediator.Send(new GetPatientQuery(id));
        
        if (!result.IsSuccess)
            return NotFound(result.Error);

        return Ok(result.Data);
    }

    [HttpGet("search")]
    [Authorize(Policy = "PatientRead")]
    [ProducesResponseType(typeof(PagedResult<PatientResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> SearchPatients([FromQuery] SearchPatientRequest request)
    {
        var result = await _mediator.Send(new SearchPatientsQuery(request));
        return Ok(result.Data);
    }

    [HttpGet("{id:guid}/encounters")]
    [Authorize(Policy = "PatientRead")]
    public async Task<IActionResult> GetPatientEncounters(Guid id)
    {
        // Implementation for retrieving encounters
        return Ok();
    }
}

// ================================================================
// Services & Infrastructure (ZFP AI-API INTEGRATION)
// ================================================================

public interface ICacheService
{
    Task<T?> GetAsync<T>(string key);
    Task SetAsync<T>(string key, T value, TimeSpan? expiration = null);
    Task RemoveAsync(string key);
}

public class RedisCacheService : ICacheService
{
    private readonly IConnectionMultiplexer _redis;
    private readonly IDatabase _db;

    public RedisCacheService(IConnectionMultiplexer redis)
    {
        _redis = redis;
        _db = redis.GetDatabase();
    }

    public async Task<T?> GetAsync<T>(string key)
    {
        var value = await _db.StringGetAsync(key);
        if (!value.HasValue) return default;
        return JsonSerializer.Deserialize<T>(value!.ToString());
    }

    public async Task SetAsync<T>(string key, T value, TimeSpan? expiration = null)
    {
        var json = JsonSerializer.Serialize(value);
        await _db.StringSetAsync(key, json, expiration);
    }

    public async Task RemoveAsync(string key)
    {
        await _db.KeyDeleteAsync(key);
    }
}

// CRITICAL: Updated to ASYNC interface to handle remote AI-API call
public interface IEncryptionService
{
    Task<byte[]?> EncryptAsync(string plaintext); // CRITICAL: Now async
    Task<string> DecryptAsync(byte[] ciphertext); // CRITICAL: Now async
}

// CRITICAL: Audit remains ASYNC interface for remote AI-API call
public interface IAuditService
{
    Task LogAsync(string action, Guid entityId, object? data = null);
}

// NEW INTERFACE: The core client for the AI-API
public interface IAiApiNegotiator
{
    // Negotiates a capability with the AI-API and returns the deserialized result object
    Task<Result<T>> NegotiateAsync<T>(string capability, object terms);
}

// NEW IMPLEMENTATION: The AI-API Client (Uses HttpClient)
public class AiApiNegotiator : IAiApiNegotiator
{
    private readonly HttpClient _client;
    private readonly ILogger<AiApiNegotiator> _logger;
    
    public AiApiNegotiator(HttpClient client, ILogger<AiApiNegotiator> logger)
    {
        _client = client;
        _logger = logger;
    }

    public async Task<Result<T>> NegotiateAsync<T>(string capability, object terms)
    {
        try
        {
            var requestPayload = new 
            {
                capability = capability,
                terms = terms
            };

            // Post to the remote AI-API endpoint
            var response = await _client.PostAsJsonAsync("negotiate", requestPayload);
            
            // Critical check for HTTP success
            response.EnsureSuccessStatusCode();

            // Read the standardized AI-API response
            var responseBody = await response.Content.ReadFromJsonAsync<Dictionary<string, JsonElement>>();

            if (responseBody == null || responseBody.GetValueOrDefault("status").GetString() != "ok")
            {
                var error = responseBody.GetValueOrDefault("error").GetString() ?? "Unknown AI-API error.";
                _logger.LogError("AI-API Negotiation failed for {Capability}: {Error}", capability, error);
                return Result<T>.Failure($"AI-API Negotiation failed for {capability}: {error}");
            }

            // Extract and deserialize the 'result' key
            if (responseBody.TryGetValue("result", out var resultElement) && resultElement.ValueKind != JsonValueKind.Null)
            {
                // Deserialize the result element into the target type T
                var finalResult = JsonSerializer.Deserialize<T>(resultElement.GetRawText());
                
                if (finalResult != null)
                    return Result<T>.Success(finalResult);
            }
            
            return Result<T>.Failure($"AI-API Negotiation failed: Could not parse result for {capability}.");
        }
        catch (HttpRequestException e)
        {
            _logger.LogCritical(e, "AI-API Negotiation CRITICAL FAILURE for {Capability}: Network or service not found!", capability);
            return Result<T>.Failure($"AI-API Negotiation CRITICAL FAILURE: Network or service not found: {e.Message}");
        }
        catch (Exception e)
        {
            _logger.LogError(e, "AI-API Negotiation failure: General exception.");
            return Result<T>.Failure($"AI-API Negotiation failure: {e.Message}");
        }
    }
}

// IMPLEMENTATION: ADAPTER for Encryption (ZFP PILLAR 4 Enforcement)
public class AiApiEncryptionAdapter : IEncryptionService
{
    private readonly IAiApiNegotiator _negotiator;

    public AiApiEncryptionAdapter(IAiApiNegotiator negotiator)
    {
        _negotiator = negotiator;
    }

    // Encrypt - Calls the remote 'data:encrypt' capability
    public async Task<byte[]?> EncryptAsync(string plaintext)
    {
        // Define the expected AI-API result type for encryption
        record EncryptionResult(string ciphertext_base64);

        var terms = new { plaintext = plaintext };
        
        // CRITICAL: Negotiate the 'data:encrypt' capability
        var result = await _negotiator.NegotiateAsync<EncryptionResult>("data:encrypt", terms);

        if (result.IsSuccess && result.Data != null && !string.IsNullOrEmpty(result.Data.ciphertext_base64))
        {
            // Z will return the encrypted bytes as a Base64 string
            return Convert.FromBase64String(result.Data.ciphertext_base64);
        }
        
        // If AI-API fails, this is a C.R.I.T.I.C.A.L failure!
        throw new InvalidOperationException($"ZFP Pillar 4 (Encrypt) Negotiation Failed: {result.Error}");
    }

    // Decrypt - Calls the remote 'data:decrypt' capability
    public Task<string> DecryptAsync(byte[] ciphertext)
    {
        // This would require a call to 'data:decrypt' in the same way.
        throw new NotImplementedException("ZFP Pillar 4 Decryption via AI-API is not implemented for this transaction.");
    }
}

// IMPLEMENTATION: ADAPTER for Audit (ZFP PILLAR 9 Enforcement)
public class AiApiAuditAdapter : IAuditService
{
    private readonly IAiApiNegotiator _negotiator;

    public AiApiAuditAdapter(IAiApiNegotiator negotiator)
    {
        _negotiator = negotiator;
    }

    public async Task LogAsync(string action, Guid entityId, object? data = null)
    {
        var terms = new 
        {
            action = action,
            entity_id = entityId,
            user_id = Guid.Empty, // Placeholder: Must be retrieved from HttpContext in a real scenario
            data = data
        };
        
        // CRITICAL: Negotiate the 'audit:log' capability
        var result = await _negotiator.NegotiateAsync<object>("audit:log", terms);
        
        if (!result.IsSuccess)
        {
            // Logging the failure is the only recourse for a failure in the Audit Pillar
            throw new InvalidOperationException($"ZFP Pillar 9 (Preserve/Audit) Negotiation Failed: {result.Error}");
        }
    }
}

// Removed original local EncryptionService and AuditService classes.

// ================================================================
// Events & Messages
// ================================================================

public class PatientCreatedEvent
{
    public Guid PatientId { get; set; }
    public string MRN { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public DateTime DateOfBirth { get; set; }
    public DateTime Timestamp { get; set; }
}

public class AuditEvent
{
    public string Action { get; set; } = string.Empty;
    public Guid EntityId { get; set; }
    public Guid UserId { get; set; }
    public DateTime Timestamp { get; set; }
    public object? Data { get; set; }
}

// ================================================================
// Result Pattern
// ================================================================

public class Result<T>
{
    public bool IsSuccess { get; private set; }
    public T? Data { get; private set; }
    public string? Error { get; private set; }

    public static Result<T> Success(T data) => new() { IsSuccess = true, Data = data };
    public static Result<T> Failure(string error) => new() { IsSuccess = false, Error = error };
}

// ================================================================
// External Placeholder (For HttpClient)
// ================================================================
// This is a placeholder for MassTransit and HttpClient policy requirements.
public interface IExternalService {}
public class ExternalService : IExternalService {}