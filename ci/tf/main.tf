terraform {
  backend "http" {
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

provider "dns" {
  update {
    server        = var.dns_server
    key_name      = var.dns_tsig_key
    key_algorithm = var.dns_tsig_algorithm
    key_secret    = var.dns_tsig_secret
  }
}

resource "tls_private_key" "this" {
  algorithm = "ED25519"
}

resource "hcloud_ssh_key" "this" {
  name       = var.name
  public_key = tls_private_key.this.public_key_openssh
}

data "hcloud_image" "this" {
  with_selector = "custom_image=archlinux"
  most_recent   = true
  with_status   = ["available"]
}

resource "hcloud_server" "this" {
  name        = var.name
  image       = data.hcloud_image.this.id
  server_type = var.server_type
  datacenter  = var.datacenter
  ssh_keys    = [hcloud_ssh_key.this.name]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
}

resource "hcloud_rdns" "this" {
  for_each = { ipv4 : hcloud_server.this.ipv4_address, ipv6 : hcloud_server.this.ipv6_address }

  server_id  = hcloud_server.this.id
  ip_address = each.value
  dns_ptr    = "${var.name}.${var.dns_zone}"
}

resource "dns_a_record_set" "this" {
  zone      = "${var.dns_zone}."
  name      = var.name
  addresses = [hcloud_server.this.ipv4_address]
  ttl       = 300
}

resource "dns_aaaa_record_set" "this" {
  zone      = "${var.dns_zone}."
  name      = var.name
  addresses = [hcloud_server.this.ipv6_address]
  ttl       = 300
}
