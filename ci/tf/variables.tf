variable "hcloud_token" {
  type      = string
  sensitive = true
}

variable "dns_server" {
  type = string
}

variable "dns_tsig_key" {
  type = string
}

variable "dns_tsig_algorithm" {
  type = string
}

variable "dns_tsig_secret" {
  type = string
}

variable "dns_zone" {
  type = string
}

variable "name" {
  type = string
}

variable "server_type" {
  type = string
}

variable "datacenter" {
  type = string
}
