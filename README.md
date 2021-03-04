# Kifurushi

[![Pypi version](https://img.shields.io/pypi/v/kifurushi.svg)](https://pypi.org/project/kifurushi/)
![](https://github.com/lewoudar/kifurushi/workflows/CI/badge.svg)
[![Coverage Status](https://codecov.io/gh/lewoudar/kifurushi/branch/main/graphs/badge.svg?branch=main)](https://codecov.io/gh/lewoudar/kifurushi)
[![Documentation Status](https://readthedocs.org/projects/kifurushi/badge/?version=latest)](https://kifurushi.readthedocs.io/en/latest/?badge=latest)
[![License Apache 2](https://img.shields.io/hexpm/l/plug.svg)](http://www.apache.org/licenses/LICENSE-2.0)

A simple library to forge network packets.

## Why?

I was playing with the DNS protocol using the excellent [scapy](https://scapy.readthedocs.io/) library.
It is very simple to forge network data with this library. I have always wondered why protocol libraries like
[h2](https://hyper-h2.readthedocs.io/en/stable/) or [aioquic](https://aioquic.readthedocs.io/en/latest/) don't use it
to forge packets instead of doing it all by hands and then I thought maybe it is because it will be overkill to import
the whole library containing many protocol implementations just for one thing you want to use (or maybe library authors
don't know the scapy library...). It would be glad to just use the scapy ability to forge packets without importing the
**huge** protocol library. This is where the idea of *kifurushi* comes from.

It is a simple library that will help you forge network data quickly. It is less capable than scapy because its specific
goal is to implement a concrete protocol as opposed to scapy which makes it possible to give free rein to its imagination.
So if you find that your needs cannot be simply express with kifurushi, you probably need to use scapy.

## Installation

with pip:

```bash
pip install kifurushi
```

With [poetry](https://python-poetry.org/docs/) an alternative package manager:

```bash
poetry add kifurushi
```

kifurushi starts working from **python3.6** and also supports **pypy3**. It has one dependency:
* [attrs](https://www.attrs.org/en/stable/): A library helping to write classes without pain.

## Documentation

The documentation is available at https://kifurushi.readthedocs.io

## Usage

```python
import socket
import enum
from kifurushi import Packet, ShortField, ByteField, IntEnumField

HOST = 'disney-stuff.com'
PORT = 14006


class Mood(enum.Enum):
  happy = 1
  cool = 2
  angry = 4


class Disney(Packet):
  __fields__ = [
    ShortField('mickey', 2),
    ByteField('minnie', 3, hex=True),
    IntEnumField('donald', 1, Mood)
  ]


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
  disney = Disney()
  s.connect((HOST, PORT))
  disney.donald = Mood.cool.value
  # we send the packet data
  s.sendall(disney.raw)
  # we create another packet object from raw bytes
  received_packet = Disney.from_bytes(s.recv(1024))
  print(received_packet)
```

To see more protocol implementations check the folder [examples](examples) of the project.

## Warnings

* If you use the excellent [Pycharm](https://www.jetbrains.com/pycharm/) editor, you may notice weird warnings when
  instantiating kifurushi fields. At the moment I'm writing this documentation, I'm using Pycharm 2020.3 and there is
  an [issue](https://youtrack.jetbrains.com/issue/PY-46298) when subclassing **attrs** classes. So just ignore the
  warning saying to fill the *format* parameter if you don't need it.
* kifurushi is a young project, so it is expected to have breaking changes in the api without respecting the 
  [semver](https://semver.org/) principle. It is recommended to pin the version you are using for now.