FROM node:alpine

WORKDIR /ui

COPY package.json ./

RUN npm install

COPY . .

CMD [ "npm", "run", "dev" ]
