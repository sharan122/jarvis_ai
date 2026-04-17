"""
Log formatting
"""
import datetime
import json
import logging
import sys
from logging import Formatter

from config.settings import config
from schemas.json_logs import BaseJsonLogSchema

LEVEL_TO_NAME = {
    logging.ERROR: "ERROR",
    logging.WARNING: "WARNING",
    logging.INFO: "INFO",
    logging.DEBUG: "DEBUG",
    logging.NOTSET: "TRACE",
}


class JsonFormatter(Formatter):
    """
    JSON log formatting
    """

    def format(self, record) -> str:
        log_object: dict = self._format_log_object(record)
        return json.dumps(log_object, ensure_ascii=False)

    @staticmethod
    def _format_log_object(record: logging.LogRecord) -> dict:
        now = (
            datetime.datetime.fromtimestamp(record.created)
            .astimezone()
            .replace(microsecond=0)
            .isoformat()
        )
        message = record.getMessage()

        json_log_fields = BaseJsonLogSchema(
            thread=record.process,
            timestamp=now,
            level_name=LEVEL_TO_NAME[record.levelno],
            message=message,
            source_log=record.name,
            app_name=config["APP_NAME"],
        )

        if hasattr(record, "correlation_id"):
            json_log_fields.correlation_id = record.correlation_id
        if hasattr(record, "props"):
            json_log_fields.props = record.props

        elif record.exc_text:
            json_log_fields.exceptions = record.exc_text

        # Pydantic to dict
        json_log_object = json_log_fields.model_dump(
            exclude_unset=True,
            by_alias=True,
        )
        # getting additional fields
        if hasattr(record, "request_json_fields"):
            json_log_object.update(record.request_json_fields)
        if hasattr(record, "response_json_fields"):
            json_log_object.update(record.response_json_fields)

        return json_log_object


logger = logging.root
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)

logging.getLogger("uvicorn.access").disabled = True
