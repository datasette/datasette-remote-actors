# datasette-remote-actors

[![PyPI](https://img.shields.io/pypi/v/datasette-remote-actors.svg)](https://pypi.org/project/datasette-remote-actors/)
[![Changelog](https://img.shields.io/github/v/release/datasette/datasette-remote-actors?include_prereleases&label=changelog)](https://github.com/datasette/datasette-remote-actors/releases)
[![Test](https://github.com/datasette/datasette-remote-actors/actions/workflows/test.yml/badge.svg)](https://github.com/datasette/datasette-remote-actors/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/datasette/datasette-remote-actors/blob/main/LICENSE)

A Datasette plugin for fetching details of actors from a remote endpoint. See [#2180](https://github.com/simonw/datasette/issues/2180) for details.

## Installation

```bash
datasette install datasette-remote-actors
```

## API endpoint

You must configure this plugin with a URL to an endpoint that returns JSON data about actors.

The endpoint should accept a comma separated list of IDs `?ids=1,2,3` and return a JSON dictionary that looks like this:

```json
{
  "1": {
    "id": "1",
    "name": "Name 1",
  },
  "2": {
    "id": "2",
    "name": "Name 2",
  }
}
```
Aside from requiring an ID (which can be a string or an integer) the content of that actor dictionary is entirely up to the implementor.

If you only have a small number of actors your endpoint could ignore the `?ids=` parameter and return all of the actors in one go. They will be cached by the plugin and used to serve future requests.

## Configuration

```yaml
plugins:
  datasette-remote-actors:
    ttl: 60
    url: https://example.com/actors.json
    token: xxx
```
The `url` is required, the others are optional.

- `url` - the URL to the endpoint that can resolve actor IDs into JSON actor dictionaries
- `ttl` - the number of seconds to cache the result for a specific actor - omit this for no caching
- `token` - an optional token to be sent in the `Authorization: Bearer xxx` header for authentication

## Integration with datasette-profiles

This plugin can also incorporate user-edited profile data from the [datasette-profiles](https://github.com/datasette/datasette-profiles) plugin. Values from that plugin will over-ride the values returned by the remote API.

To enable that feature, install `datasette-profiles` and add `datasette-profiles: true` to this plugin's configuration.

```yaml
plugins:
  datasette-remote-actors:
    url: https://example.com/actors.json
    datasette-profiles: true
```

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd datasette-remote-actors
python3 -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```
