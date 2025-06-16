# InfluxDB Operator Charm
This charm provides InfluxDB v1 as a charmed service.


## Getting Started
Use [`juju`](https://juju.is) to deploy this charm.

```bash
juju deploy influxdb --channel edge
```

Use `juju status` to inspect the deployment.
```bash
Model     Controller           Cloud/Region         Version  SLA          Timestamp
influxdb  localhost-localhost  localhost/localhost  3.6.7    unsupported  21:42:59Z

App       Version    Status  Scale  Charm     Channel  Rev  Exposed  Message
influxdb  1.6.7~rc0  active      1  influxdb             0  no

Unit         Workload  Agent  Machine  Public address  Ports     Message
influxdb/0*  active    idle   0        192.168.7.189   8086/tcp

Machine  State    Address        Inst id        Base          AZ  Message
0        started  192.168.7.189  juju-95c95f-0  ubuntu@24.04      Running
```

## Charm Actions

### `get-admin-password`
Retrieve the admin password for influxdb using the in-built charm action `get-admin-password`.

```bash
juju run influxdb/leader get-admin-password
```

## Add User



