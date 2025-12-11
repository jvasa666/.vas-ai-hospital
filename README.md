# 🏥 VAS-AI-Hospital

**Enterprise Hospital Management System with ZFP Causal Anchor AI Integration**

[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

> **One-command deployment. Production-ready. HIPAA-compliant. AI-powered clinical decision support.**

---

## 🚀 Quick Start (3 Minutes)

### Linux/WSL/macOS:
```bash
git clone https://github.com/jvasa666/.vas-ai-hospital.git
cd .vas-ai-hospital
./vas-simple-install.sh
```

### Windows PowerShell:
```powershell
git clone https://github.com/jvasa666/.vas-ai-hospital.git
cd .vas-ai-hospital
.\vas-simple-install.ps1
```

**That's it!** 🎉 Your hospital management system is now running.

Access at: **http://localhost:3001**

---

## 📋 What You Get

- ✅ **15+ Microservices** (Patient, Clinical, Admin, Analytics)
- ✅ **AI-Gateway** - ZFP Causal Anchor capability router
- ✅ **100 Demo Patients** - Ready for live demonstrations
- ✅ **Real-time AI Features:**
  - Sepsis risk prediction (6 hours ahead)
  - Drug interaction detection
  - 30-day readmission forecasting
- ✅ **HIPAA Compliant** - PHI encryption, immutable audit logs
- ✅ **Production Ready** - PostgreSQL, Redis, MinIO, Docker

---

## 🛠️ Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **8GB RAM** minimum (16GB recommended)
- **20GB** free disk space
- **Internet connection** (for first-time image pulls)

---

## 📊 Service Endpoints

| Service | Port | Endpoint | Description |
|:--------|:----:|:---------|:------------|
| AI-Gateway | 8888 | http://localhost:8888 | Capability router |
| Patient Service | 8081 | http://localhost:8081 | Patient management |
| Clinical Service | 8082 | http://localhost:8082 | Clinical operations |
| Admin Service | 8083 | http://localhost:8083 | User administration |
| Analytics | 8084 | http://localhost:8084 | BI & forecasting |
| Staff Dashboard | 3001 | http://localhost:3001 | Web UI |

---

## 🧪 Testing

### Quick Health Check
```bash
curl http://localhost:8888/capabilities  # AI-Gateway
curl http://localhost:8081/api/health    # Patient Service
```

### Test AI Capabilities
```bash
# Encrypt PHI data
curl -X POST http://localhost:8888/invoke \
  -H "Content-Type: application/json" \
  -d '{"capability":"data:encrypt","terms":{"plaintext":"123-45-6789"}}'
```

---

## 🔧 Management Commands
```bash
# View logs
docker compose -f docker-compose.vas.yml logs -f

# Stop all services
docker compose -f docker-compose.vas.yml down

# Restart
docker compose -f docker-compose.vas.yml restart
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Made with ❤️ by the VAS team**

⭐ **Star this repo** if you find it useful!
