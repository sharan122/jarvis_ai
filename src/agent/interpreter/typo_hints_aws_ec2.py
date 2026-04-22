"""
AWS EC2 typo hints.

Covers common informal / misspelled inputs for every field in the
aws_ec2 service config.  Imported dynamically by typo_hints.py — never
import this file directly in application code.
"""

from __future__ import annotations

HINTS: dict[str, dict[str, str]] = {

    "environment": {
        "development":     "DEV",
        "develop":         "DEV",
        "dev environment": "DEV",
        "quality":         "QA",
        "quality assurance": "QA",
        "test":            "QA",
        "testing":         "QA",
        "staging":         "QA",
        "production":      "PROD",
        "prod environment": "PROD",
        "live":            "PROD",
    },

    "region": {
        # US East 1
        "us east 1":    "us-east-1",
        "us-east1":     "us-east-1",
        "useast1":      "us-east-1",
        "us east":      "us-east-1",
        "virginia":     "us-east-1",
        "n. virginia":  "us-east-1",
        "north virginia": "us-east-1",
        # US East 2
        "us east 2":    "us-east-2",
        "us-east2":     "us-east-2",
        "useast2":      "us-east-2",
        "ohio":         "us-east-2",
        # EU West 1
        "eu west 1":    "eu-west-1",
        "eu-west1":     "eu-west-1",
        "euwest1":      "eu-west-1",
        "ireland":      "eu-west-1",
        "europe":       "eu-west-1",
        # AP South 1
        "ap south 1":   "ap-south-1",
        "ap-south1":    "ap-south-1",
        "apsouth1":     "ap-south-1",
        "india":        "ap-south-1",
        "mumbai":       "ap-south-1",
    },

    "availability_zone": {
        # US East 1
        "us east 1a":   "us-east-1a",
        "us east 1b":   "us-east-1b",
        "us east 1c":   "us-east-1c",
        "use1a":        "us-east-1a",
        "use1b":        "us-east-1b",
        # US East 2
        "us east 2a":   "us-east-2a",
        "us east 2b":   "us-east-2b",
        "use2a":        "us-east-2a",
        # EU West 1
        "eu west 1a":   "eu-west-1a",
        "eu west 1b":   "eu-west-1b",
        # AP South 1
        "ap south 1a":  "ap-south-1a",
        "ap south 1b":  "ap-south-1b",
    },

    "instance_type": {
        # t3 family
        "t3 small":     "t3.small",
        "t3small":      "t3.small",
        "t3 medium":    "t3.medium",
        "t3medium":     "t3.medium",
        "small":        "t3.small",
        "medium":       "t3.medium",
        # m5 family
        "m5 large":     "m5.large",
        "m5large":      "m5.large",
        "m5 xlarge":    "m5.xlarge",
        "m5xlarge":     "m5.xlarge",
        "large":        "m5.large",
        "xlarge":       "m5.xlarge",
        "extra large":  "m5.xlarge",
        # c5 family
        "c5 large":     "c5.large",
        "c5large":      "c5.large",
        "compute large": "c5.large",
    },

    "ami": {
        # Ubuntu patterns
        "ubuntu":           "ami-ubuntu-2204-use1",
        "ubuntu 22":        "ami-ubuntu-2204-use1",
        "ubuntu 22.04":     "ami-ubuntu-2204-use1",
        "ubuntu 2204":      "ami-ubuntu-2204-use1",
        # Amazon Linux patterns
        "amazon linux":     "ami-amazonlinux2-use1",
        "amazon linux 2":   "ami-amazonlinux2-use1",
        "amazonlinux":      "ami-amazonlinux2-use1",
        "amzn2":            "ami-amazonlinux2-use1",
        "al2":              "ami-amazonlinux2-use1",
    },

    "compute_type": {
        "general":          "general-purpose",
        "gp":               "general-purpose",
        "general purpose":  "general-purpose",
        "balanced":         "general-purpose",
        "memory":           "memory-optimized",
        "memory optimized": "memory-optimized",
        "high memory":      "memory-optimized",
        "ram":              "memory-optimized",
        "compute":          "compute-optimized",
        "compute optimized": "compute-optimized",
        "cpu":              "compute-optimized",
        "high cpu":         "compute-optimized",
    },

    "disk_size_gb": {
        # Keywords → boundary values (AWS: min 20, max 500)
        "min":      "20",
        "minimum":  "20",
        "default":  "20",
        "smallest": "20",
        "lowest":   "20",
        "least":    "20",
        "max":      "500",
        "maximum":  "500",
        "largest":  "500",
        "highest":  "500",
        "full":     "500",
        # English number words
        "twenty":              "20",
        "thirty":              "30",
        "forty":               "40",
        "fifty":               "50",
        "sixty":               "60",
        "seventy":             "70",
        "eighty":              "80",
        "ninety":              "90",
        "hundred":             "100",
        "one hundred":         "100",
        "one hundred fifty":   "150",
        "one fifty":           "150",
        "two hundred":         "200",
        "two fifty":           "250",
        "two hundred fifty":   "250",
        "three hundred":       "300",
        "three fifty":         "350",
        "four hundred":        "400",
        "four fifty":          "450",
        "five hundred":        "500",
        # With unit suffix
        "20 gb": "20",   "20gb": "20",   "20 gigabytes": "20",
        "30 gb": "30",   "30gb": "30",   "30 gigabytes": "30",
        "50 gb": "50",   "50gb": "50",   "50 gigabytes": "50",
        "100 gb": "100", "100gb": "100", "100 gigabytes": "100",
        "150 gb": "150", "150gb": "150",
        "200 gb": "200", "200gb": "200", "200 gigabytes": "200",
        "250 gb": "250", "250gb": "250",
        "300 gb": "300", "300gb": "300",
        "400 gb": "400", "400gb": "400",
        "500 gb": "500", "500gb": "500", "500 gigabytes": "500",
    },
}
