# InfluxDB Operator Charm

This charm provides [InfluxDB v1](https://docs.influxdata.com/influxdb/v1.8/introduction/overview/) as a Charmed Operator, enabling lifecycle management and administrative operations via [Juju](https://juju.is).

---

## 🚀 Getting Started

To deploy the InfluxDB charm:

```bash
juju deploy influxdb --channel edge
```

You can inspect the deployment status with:

```bash
juju status
```

Sample output:
```
Model     Controller           Cloud/Region         Version  SLA          Timestamp
influxdb  localhost-localhost  localhost/localhost  3.6.7    unsupported  21:42:59Z

App       Version    Status  Scale  Charm     Channel  Rev  Exposed  Message
influxdb  1.6.7~rc0  active      1  influxdb             0  no

Unit         Workload  Agent  Machine  Public address  Ports     Message
influxdb/0*  active    idle   0        192.168.7.189   8086/tcp

Machine  State    Address        Inst id        Base          AZ  Message
0        started  192.168.7.189  juju-95c95f-0  ubuntu@24.04      Running
```

---

## ⚙️ Charm Features

This charm offers fine-grained control over InfluxDB, including:

- User management (create, delete, update passwords, list)
- Database management (create, delete, list)
- Privilege control (grant/revoke/read privileges)
- Secure password storage using Juju secrets

All features are accessible via [Juju actions](https://juju.is/docs/juju/actions).

---

## 🔐 User Management

### Create a User

```bash
juju run influxdb/leader create-user username=<username>
```

This creates a user with a generated password stored as a Juju secret.

### Delete a User

```bash
juju run influxdb/leader drop-user username=<username>
```

### List Users

```bash
juju run influxdb/leader list-users
```

### Update User Password

```bash
juju run influxdb/leader update-user-password username=<username> password=<new-password>
```

### Get User Password

```bash
juju run influxdb/leader get-user-password username=<username>
```

---

## 🗃️ Database Management

### Create a Database

```bash
juju run influxdb/leader create-database database=<database-name>
```

### Delete a Database

```bash
juju run influxdb/leader drop-database database=<database-name>
```

### List Databases

```bash
juju run influxdb/leader list-databases
```

---

## 🔐 Privilege Management

### Grant Privilege

```bash
juju run influxdb/leader grant-privilege \
    username=<username> \
    database=<database-name> \
    permission=read|write|all
```

### Revoke Privilege

```bash
juju run influxdb/leader revoke-privilege \
    username=<username> \
    database=<database-name> \
    permission=read|write|all
```

### List User Privileges

```bash
juju run influxdb/leader list-privileges username=<username>
```

---

## 🔑 Admin Password

Retrieve the administrator password securely:

```bash
juju run influxdb/leader get-admin-password
```

---

## 📦 Project Structure

The charm uses the `astral-uv` plugin and is designed for Ubuntu 24.04:

```yaml
parts:
  influxdb:
    source: .
    plugin: uv
    build-snaps:
      - astral-uv
```

---

## 🔗 Useful Links

- 💬 Community Chat: [#hpc:ubuntu.com](https://matrix.to/#/#hpc:ubuntu.com)
- 🐛 Report Issues: [influxdb-operator/issues](https://github.com/charmed-hpc/influxdb-operator/issues)
- 🔍 Source Code: [charmed-hpc/influxdb-operator](https://github.com/charmed-hpc/influxdb-operator)

