1. copy config_sample.json to config.json and set variables appropriately (note: HOST and PORT will only be used if the client doesn't supply an HTTP Host header)
2. `python app.py <CM_DIR>/out/target/product`
3. set `cm.updater.uri` to `http://HOST:PORT/api`
4. profit
