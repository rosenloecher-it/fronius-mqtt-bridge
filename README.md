# fronius-mqtt-bridge

TODO

## Startup

### Prepare python environment
```bash
cd /opt
sudo mkdir fronius-mqtt-bridge
sudo chown <user>:<user> fronius-mqtt-bridge  # type in your user
git clone https://github.com/rosenloecher-it/fronius-mqtt-bridge fronius-mqtt-bridge

cd fronius-mqtt-bridge
virtualenv -p /usr/bin/python3 venv

# activate venv
source ./venv/bin/activate

# check python version >= 3.7
python --version

# install required packages
pip install -r requirements.txt
```

### Configuration

```bash
# cd ... goto project dir
cp ./fronius-mqtt-bridge.yaml.sample ./fronius-mqtt-bridge.yaml

# security concerns: make sure, no one can read the stored passwords
chmod 600 ./fronius-mqtt-bridge.yaml
```

Edit your `fronius-mqtt-bridge.yaml`. See comments there.

### Run

```bash
# see command line options
./fronius-mqtt-bridge.sh --help

# prepare your own config file based on ./fronius-mqtt-bridge.yaml.sample
# the embedded json schema may contain additional information
./fronius-mqtt-bridge.sh --json-schema

# start the logger
./fronius-mqtt-bridge.sh --print-logs --config-file ./fronius-mqtt-bridge.yaml
# abort with ctrl+c

```

## Register as systemd service
```bash
# prepare your own service script based on fronius-mqtt-bridge.service.sample
cp ./fronius-mqtt-bridge.service.sample ./fronius-mqtt-bridge.service

# edit/adapt pathes and user in fronius-mqtt-bridge.service
vi ./fronius-mqtt-bridge.service

# install service
sudo cp ./fronius-mqtt-bridge.service /etc/systemd/system/
# alternativ: sudo cp ./fronius-mqtt-bridge.service.sample /etc/systemd/system//fronius-mqtt-bridge.service
# after changes
sudo systemctl daemon-reload

# start service
sudo systemctl start fronius-mqtt-bridge

# check logs
journalctl -u fronius-mqtt-bridge
journalctl -u fronius-mqtt-bridge --no-pager --since "5 minutes ago"

# enable autostart at boot time
sudo systemctl enable fronius-mqtt-bridge.service
```

## Additional infos

### MQTT broker related infos

If no messages get logged check your broker.
```bash
sudo apt-get install mosquitto-clients

# preprare credentials
SERVER="<your server>"

# start listener
mosquitto_sub -h $SERVER -d -t smarthome/#

# send single message
mosquitto_pub -h $SERVER -d -t smarthome/test -m "test_$(date)"

# just as info: clear retained messages
mosquitto_pub -h $SERVER -d -t smarthome/test -n -r -d
```

## Maintainer & License

MIT © [Raul Rosenlöcher](https://github.com/rosenloecher-it)

The code is available at [GitHub][home].

[home]: https://github.com/rosenloecher-it/fronius-mqtt-bridge
