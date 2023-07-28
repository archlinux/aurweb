terraform {
  required_providers {
    tls = {
      source = "hashicorp/tls"
    }
    hcloud = {
      source = "hetznercloud/hcloud"
    }
    dns = {
      source = "hashicorp/dns"
    }
  }
}
