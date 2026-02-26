FROM node:20-alpine

WORKDIR /app/front

COPY front/package*.json ./
RUN npm install

COPY front/ ./

EXPOSE 9919

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "9919"]
