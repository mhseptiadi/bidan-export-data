from django.db import models
from django.utils import timezone
import datetime

class Response(models.Model):
	response_text = models.TextField()
	response_username = models.CharField(max_length=200)
	response_password = models.CharField(max_length=200)
	def __str__(self):
		return self.response_username
	@classmethod
	def create(cls, response_text, response_username, response_password):
		response = cls(response_text=response_text, response_username=response_username, response_password=response_password)
		# do something with the book
		return response
