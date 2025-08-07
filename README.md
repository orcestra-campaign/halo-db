# HALO Download Bot

## Usage

To access the [HALO DB](http://halo-db.pa.op.dlr.de), create a file `~/.halodb` with the following content:

```json
{
    "email": "<your e-mail address>",
    "password": "<your password>"
}
```

Afterwards, you can download all the datasets for a given mission by specifying its mission ID:
```sh
uv run halo-db.py -m 141
```
