"""
AWS RDS typo hints.

Covers common informal / misspelled inputs for every field in the
aws_rds service config.  Imported dynamically by typo_hints.py — never
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
        "us east 1a":  "us-east-1a",
        "us east 1b":  "us-east-1b",
        "us east 1c":  "us-east-1c",
        "use1a":       "us-east-1a",
        "use1b":       "us-east-1b",
        # US East 2
        "us east 2a":  "us-east-2a",
        "us east 2b":  "us-east-2b",
        "use2a":       "us-east-2a",
        # EU West 1
        "eu west 1a":  "eu-west-1a",
        "eu west 1b":  "eu-west-1b",
        # AP South 1
        "ap south 1a": "ap-south-1a",
        "ap south 1b": "ap-south-1b",
    },

    "db_engine": {
        # MySQL
        "mysql":          "mysql",
        "my sql":         "mysql",
        "mysql db":       "mysql",
        # PostgreSQL
        "postgres":       "postgres",
        "postgresql":     "postgres",
        "postgre":        "postgres",
        "psql":           "postgres",
        "pg":             "postgres",
        # MariaDB
        "mariadb":        "mariadb",
        "maria db":       "mariadb",
        "maria":          "mariadb",
        # Oracle
        "oracle":         "oracle-se2",
        "oracle se2":     "oracle-se2",
        "oracle-se2":     "oracle-se2",
        "oracle standard":"oracle-se2",
        # SQL Server
        "sqlserver":      "sqlserver-se",
        "sql server":     "sqlserver-se",
        "mssql":          "sqlserver-se",
        "ms sql":         "sqlserver-se",
        "microsoft sql":  "sqlserver-se",
        "sql server se":  "sqlserver-se",
    },

    "db_engine_version": {
        # MySQL
        "8.0":   "8.0.36",
        "8":     "8.0.36",
        "5.7":   "5.7.44",
        "latest mysql": "8.0.36",
        # PostgreSQL
        "16":    "16.2",
        "15":    "15.6",
        "14":    "14.11",
        "13":    "13.14",
        "latest postgres": "16.2",
        "latest postgresql": "16.2",
        # MariaDB
        "10.11": "10.11.7",
        "10.6":  "10.6.17",
        "10.5":  "10.5.23",
        "latest mariadb": "10.11.7",
    },

    "db_instance_class": {
        # t3 family (burstable)
        "t3 micro":     "db.t3.micro",
        "t3micro":      "db.t3.micro",
        "micro":        "db.t3.micro",
        "smallest":     "db.t3.micro",
        "t3 small":     "db.t3.small",
        "t3small":      "db.t3.small",
        "small":        "db.t3.small",
        "t3 medium":    "db.t3.medium",
        "t3medium":     "db.t3.medium",
        "medium":       "db.t3.medium",
        # m5 family (general purpose)
        "m5 large":     "db.m5.large",
        "m5large":      "db.m5.large",
        "large":        "db.m5.large",
        "m5 xlarge":    "db.m5.xlarge",
        "m5xlarge":     "db.m5.xlarge",
        "xlarge":       "db.m5.xlarge",
        "extra large":  "db.m5.xlarge",
        "m5 2xlarge":   "db.m5.2xlarge",
        "m5 2x":        "db.m5.2xlarge",
        "2xlarge":      "db.m5.2xlarge",
        # r5 family (memory optimized)
        "r5 large":     "db.r5.large",
        "r5large":      "db.r5.large",
        "memory large": "db.r5.large",
        "r5 xlarge":    "db.r5.xlarge",
        "r5xlarge":     "db.r5.xlarge",
        "memory xlarge":"db.r5.xlarge",
    },

    "multi_az": {
        # True aliases
        "yes":      "true",
        "y":        "true",
        "enabled":  "true",
        "enable":   "true",
        "on":       "true",
        "1":        "true",
        "ha":       "true",
        "high availability": "true",
        "failover": "true",
        # False aliases
        "no":       "false",
        "n":        "false",
        "disabled": "false",
        "disable":  "false",
        "off":      "false",
        "0":        "false",
        "single":   "false",
        "single az":"false",
    },

    "storage_type": {
        # gp3
        "gp3":              "gp3",
        "general purpose 3":"gp3",
        "general purpose v3":"gp3",
        "ssd":              "gp3",
        "default":          "gp3",
        "standard ssd":     "gp3",
        # gp2
        "gp2":              "gp2",
        "general purpose 2":"gp2",
        "general purpose v2":"gp2",
        "old ssd":          "gp2",
        # io1 (provisioned IOPS)
        "io1":              "io1",
        "iops":             "io1",
        "provisioned iops": "io1",
        "high iops":        "io1",
        "high performance": "io1",
        "piops":            "io1",
        # standard (magnetic)
        "standard":         "standard",
        "magnetic":         "standard",
        "hdd":              "standard",
        "legacy":           "standard",
    },

    "allocated_storage_gb": {
        # Keywords → boundary values (RDS: min 20, max 65536)
        "min":       "20",
        "minimum":   "20",
        "default":   "20",
        "smallest":  "20",
        "max":       "65536",
        "maximum":   "65536",
        "largest":   "65536",
        # Common sizes with English words
        "twenty":          "20",
        "fifty":           "50",
        "hundred":         "100",
        "one hundred":     "100",
        "two hundred":     "200",
        "five hundred":    "500",
        "one thousand":    "1000",
        "one tb":          "1000",
        "two tb":          "2000",
        "five tb":         "5000",
        # With unit suffix
        "20 gb":   "20",   "20gb":   "20",
        "50 gb":   "50",   "50gb":   "50",
        "100 gb":  "100",  "100gb":  "100",
        "200 gb":  "200",  "200gb":  "200",
        "500 gb":  "500",  "500gb":  "500",
        "1 tb":    "1000", "1tb":    "1000",
        "2 tb":    "2000", "2tb":    "2000",
        "5 tb":    "5000", "5tb":    "5000",
        "10 tb":   "10000","10tb":   "10000",
    },
}
