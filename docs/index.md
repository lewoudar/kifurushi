# Welcome to kifurushi documentation

A simple library to forge network packets.

## Why kifurushi?

I was playing with the DNS protocol using the excellent [scapy](https://scapy.readthedocs.io/) library. It is very
simple to forge network data with this library. I have always wondered why protocol libraries like
[h2](https://hyper-h2.readthedocs.io/en/stable/) or [aioquic](https://aioquic.readthedocs.io/en/latest/) don't use it to
forge packets instead of doing it all by hands and then I thought maybe it is because it will be overkill to import the
whole library containing many protocol implementations just for one thing you want to use (or maybe library authors
don't know the scapy library...). It would be glad to just use the scapy ability to forge packets without importing the
**huge** protocol library. This is where the idea of *kifurushi* comes from.

It is a simple library that will help you forge network data quickly. It is less capable than scapy because its specific
goal is to implement a concrete protocol as opposed to scapy which makes it possible to give free rein to our
imagination. So if you find that your needs cannot be simply express with kifurushi, you probably need to use scapy.
