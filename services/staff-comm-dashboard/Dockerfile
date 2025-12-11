FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache wget curl

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/api/health || exit 1

CMD ["npm", "start"]
