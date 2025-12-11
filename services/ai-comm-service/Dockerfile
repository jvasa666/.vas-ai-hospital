FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache wget curl

COPY package*.json ./
RUN npm install --production

COPY src ./src
RUN mkdir -p logs && chmod 777 logs

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3001/health || exit 1

CMD ["node", "src/index.js"]
