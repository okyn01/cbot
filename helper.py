import time
import datetime
import math

def formatFloat(number):
	"""Format a number to string with 8 decimals"""
	number = format(float(number), '0.8f')
	return number

def diff(old, new):
	"""Percentage difference between 2 numbers"""
	return format((((float(new)-float(old)) / abs(float(old))) * 100), '0.2f')

def convertTime(unixTime):
	"""Convert unix time to a readable date time"""
	return datetime.datetime.fromtimestamp(float(unixTime)).strftime('%d-%m-%Y %H:%M:%S')

def roundPrice(buyPrice, tickSize):
	"""Round down a price using binance tick size"""
	buyPrice = float(buyPrice)
	tickSize = float(tickSize)
	buyPrice = buyPrice - (buyPrice % tickSize)
	buyPrice = format(buyPrice, '.8f')
	return buyPrice

def roundAmount(buyPrice, balance, stepSize):
	"""Round down an amount using binance step size"""
	buyPrice = float(buyPrice)
	balance = float(balance)
	stepSize = float(stepSize)
	amount = (balance / buyPrice) - (balance / buyPrice % stepSize)
	amount = format(amount, '.8f')
	return amount

def localTime():
	"""Gives local time in a readable format"""
	return convertTime(time.time())

def addLog(args):
	"""Add string to log"""
	f = open('log.txt','a')
	f.write('{0},\n'.format(args))
	f.close()