"""
Azure VM typo hints.

Covers common informal / misspelled inputs for every field in the
azure_vm service config.  Imported dynamically by typo_hints.py — never
import this file directly in application code.
"""

from __future__ import annotations

HINTS: dict[str, dict[str, str]] = {

    "environment": {
        "development":       "DEV",
        "develop":           "DEV",
        "dev environment":   "DEV",
        "quality":           "QA",
        "quality assurance": "QA",
        "test":              "QA",
        "testing":           "QA",
        "staging":           "QA",
        "production":        "PROD",
        "prod environment":  "PROD",
        "live":              "PROD",
    },

    "region": {
        # East US
        "east us":          "eastus",
        "east-us":          "eastus",
        "us east":          "eastus",
        "virginia":         "eastus",
        "east us 1":        "eastus",
        # East US 2
        "east us 2":        "eastus2",
        "east-us-2":        "eastus2",
        "eastus 2":         "eastus2",
        # West Europe
        "west europe":      "westeurope",
        "west-europe":      "westeurope",
        "europe":           "westeurope",
        "netherlands":      "westeurope",
        "amsterdam":        "westeurope",
        # Southeast Asia
        "southeast asia":   "southeastasia",
        "south east asia":  "southeastasia",
        "southeast-asia":   "southeastasia",
        "singapore":        "southeastasia",
        "asia":             "southeastasia",
    },

    "availability_zone": {
        # Numeric aliases — Azure zones are "1", "2", "3"
        "zone 1":   "1",
        "zone1":    "1",
        "az1":      "1",
        "az-1":     "1",
        "first":    "1",
        "one":      "1",
        "zone 2":   "2",
        "zone2":    "2",
        "az2":      "2",
        "az-2":     "2",
        "second":   "2",
        "two":      "2",
        "zone 3":   "3",
        "zone3":    "3",
        "az3":      "3",
        "az-3":     "3",
        "third":    "3",
        "three":    "3",
    },

    "vm_size": {
        # Standard_B family (burstable)
        "b2s":              "Standard_B2s",
        "standard b2s":     "Standard_B2s",
        "b2":               "Standard_B2s",
        "small":            "Standard_B2s",
        "burstable small":  "Standard_B2s",
        "b4ms":             "Standard_B4ms",
        "standard b4ms":    "Standard_B4ms",
        "b4":               "Standard_B4ms",
        "medium":           "Standard_B4ms",
        "burstable medium": "Standard_B4ms",
        # Standard_D family (general purpose)
        "d4s":              "Standard_D4s_v5",
        "d4s v5":           "Standard_D4s_v5",
        "standard d4s":     "Standard_D4s_v5",
        "d4":               "Standard_D4s_v5",
        "general purpose":  "Standard_D4s_v5",
        "d8s":              "Standard_D8s_v5",
        "d8s v5":           "Standard_D8s_v5",
        "standard d8s":     "Standard_D8s_v5",
        "d8":               "Standard_D8s_v5",
        "large":            "Standard_D8s_v5",
        # Standard_F family (compute optimised)
        "f4s":              "Standard_F4s_v2",
        "f4s v2":           "Standard_F4s_v2",
        "standard f4s":     "Standard_F4s_v2",
        "f4":               "Standard_F4s_v2",
        "compute":          "Standard_F4s_v2",
        "compute optimized": "Standard_F4s_v2",
        "cpu optimized":    "Standard_F4s_v2",
    },

    "image": {
        # Ubuntu patterns — default to eastus as the region-neutral hint
        "ubuntu":           "Ubuntu2204-eastus",
        "ubuntu 22":        "Ubuntu2204-eastus",
        "ubuntu 22.04":     "Ubuntu2204-eastus",
        "ubuntu 2204":      "Ubuntu2204-eastus",
        "ubuntu lts":       "Ubuntu2204-eastus",
        "linux":            "Ubuntu2204-eastus",
        # Windows Server patterns
        "windows":          "WindowsServer2022-eastus",
        "windows server":   "WindowsServer2022-eastus",
        "windows 2022":     "WindowsServer2022-eastus",
        "win server":       "WindowsServer2022-eastus",
        "win2022":          "WindowsServer2022-eastus",
        "ws2022":           "WindowsServer2022-eastus",
    },

    "compute_type": {
        "general":           "general-purpose",
        "gp":                "general-purpose",
        "general purpose":   "general-purpose",
        "balanced":          "general-purpose",
        "memory":            "memory-optimized",
        "memory optimized":  "memory-optimized",
        "high memory":       "memory-optimized",
        "ram":               "memory-optimized",
        "compute":           "compute-optimized",
        "compute optimized": "compute-optimized",
        "cpu":               "compute-optimized",
        "high cpu":          "compute-optimized",
    },

    "disk_size_gb": {
        # Keywords → boundary values (Azure: min 32, max 1024)
        "min":      "32",
        "minimum":  "32",
        "default":  "32",
        "smallest": "32",
        "lowest":   "32",
        "least":    "32",
        "max":      "1024",
        "maximum":  "1024",
        "largest":  "1024",
        "highest":  "1024",
        "full":     "1024",
        # English number words
        "thirty two":          "32",
        "thirty-two":          "32",
        "sixty four":          "64",
        "sixty-four":          "64",
        "hundred":             "100",
        "one hundred":         "100",
        "one hundred twenty eight": "128",
        "one twenty eight":    "128",
        "two hundred":         "200",
        "two fifty":           "250",
        "two hundred fifty":   "250",
        "two fifty six":       "256",
        "five hundred":        "500",
        "five twelve":         "512",
        "five hundred twelve":  "512",
        "one thousand":        "1000",
        "one thousand twenty four": "1024",
        # With unit suffix
        "32 gb":   "32",   "32gb":   "32",   "32 gigabytes":   "32",
        "64 gb":   "64",   "64gb":   "64",   "64 gigabytes":   "64",
        "100 gb":  "100",  "100gb":  "100",  "100 gigabytes":  "100",
        "128 gb":  "128",  "128gb":  "128",  "128 gigabytes":  "128",
        "200 gb":  "200",  "200gb":  "200",
        "256 gb":  "256",  "256gb":  "256",
        "500 gb":  "500",  "500gb":  "500",
        "512 gb":  "512",  "512gb":  "512",
        "1024 gb": "1024", "1024gb": "1024", "1 tb": "1024",   "1tb": "1024",
    },
}
