import logging
import logging.config

LOGGING_CONFIG = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'colorful': {
			'()': 'colorlog.ColoredFormatter',
			'format': '%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s',
			'log_colors': {
				'DEBUG': 'cyan',
				'INFO': 'green',
				'WARNING': 'yellow',
				'ERROR': 'bold_red',
				'CRITICAL': 'bold_red',
			},
		},
	},
	'handlers': {
		'console': {'level': 'INFO', 'class': 'logging.StreamHandler', 'formatter': 'colorful'},
	},
	'loggers': {
		'': {  # root logger
			'handlers': ['console'],
			'level': 'INFO',
			'propagate': True,
		},
	},
}


def setup_logging():
	"""Set up logging based on the configuration."""
	if not logging.getLogger().hasHandlers():
		logging.config.dictConfig(LOGGING_CONFIG)
