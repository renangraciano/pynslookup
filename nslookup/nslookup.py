#!/usr/bin/env python3
import sys

import dns.resolver, dns.exception


class DNSresponse:
    """data object for DNS answer
    response_full - full DNS response raw
    answer - DNS answer to the query
    """
    def __init__(self, response_full=[], answer=[]):
        self.response_full = response_full
        self.answer = answer


class Nslookup:
    """Object for initializing DNS resolver, with optional specific DNS servers"""
    def __init__(self, dns_servers=[], verbose=True, tcp=False):
        self.dns_resolver = dns.resolver.Resolver()
        self.verbose = verbose

        if tcp:
            print("Warning: using TCP mode with multiple requests will open a new session for each request.\n\
For large number of requests or iterative requests, it may be better to use the granular dnspython dns.query API.", file=sys.stderr)
        self.tcp = tcp

        if dns_servers:
            self.dns_resolver.nameservers = dns_servers


    def base_lookup(self, domain, record_type):
        """Get the DNS record for the given domain and type, handling errors"""
        try:
            answer = self.dns_resolver.resolve(domain, rdtype=record_type, tcp=self.tcp)
            return answer
        except dns.resolver.NXDOMAIN:
            # the domain does not exist so dns resolutions remain empty
            pass
        except dns.resolver.NoAnswer as e:
            # domains existing but not having AAAA records is common
            if self.verbose and record_type != 'AAAA':
                print("Warning:", e, file=sys.stderr)
        except dns.resolver.NoNameservers as e:
            if self.verbose:
                print("Warning:", e, file=sys.stderr)
        except dns.exception.DNSException as e:
            if self.verbose:
                print("Error: DNS exception occurred looking up '{}':".format(domain), e, file=sys.stderr)


    def dns_host_lookup(self, domain, record_type, include_cname=False):
        if record_type in ['A','AAAA']:
            dns_answer = self.base_lookup(domain, record_type)
            if dns_answer:
                dns_response = [answer.to_text() for answer in dns_answer.response.answer]
                ips = [ip.address for ip in dns_answer]
                if include_cname:
                    ips += [dns_answer.canonical_name.to_text()]
                return DNSresponse(dns_response, ips)
        else:
            raise ValueError("Expected record_type 'A' or 'AAAA'")

        return DNSresponse()


    def dns_lookup(self, domain, include_cname=False):
        return self.dns_host_lookup(domain, "A", include_cname)


    def dns_lookup6(self, domain, include_cname=False):
        return self.dns_host_lookup(domain, "AAAA", include_cname)


    def dns_lookup_all(self, domain, include_cname=False):
        resp_a = self.dns_lookup(domain, include_cname)
        resp_aaaa = self.dns_lookup6(domain, include_cname)
        return DNSresponse([*resp_a.response_full,*resp_aaaa.response_full], [*resp_a.answer,*resp_aaaa.answer])


    def soa_lookup(self, domain):
        soa_answer = self.base_lookup(domain, "SOA")
        if soa_answer:
            soa_response = [answer.to_text() for answer in soa_answer.response.answer]
            soa = [next(answer.__iter__()).to_text() for answer in soa_answer.response.answer]
            return DNSresponse(soa_response, soa)
        return DNSresponse()
