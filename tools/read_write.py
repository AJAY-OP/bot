import ast
from encryption_tools import encode, decode
import os
import motor.motor_asyncio

mongo_link = os.getenv('mlab_link') + '?retryWrites=false'
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_link)
db = client.Data
main_collection = db.main_collection
print(main_collection.find_one(), 'hi')
key = os.environ.get('KEY')


class data:
	class cache:
		def __init__(self):
			self.data = {}

		def cache(self, key, data):
			'''Add data to cache'''
			self.data[key] = data

		def read_cache(self, key):
			cache = self.data
			if key in cache:
				return cache[key]

		def check_cache(self, key):
			cache = self.data
			return key in cache


cache = data.cache()


async def read(src, lEval=True, decrypt=True, read_from_cache=True):
	is_cached = cache.check_cache(src)
	if is_cached and read_from_cache:
		data = cache.read_cache(src)
		if isinstance(data, str):
			try:
				data = ast.literal_eval(data)
			except ValueError:
				pass
			except SyntaxError:
				pass
		return data
	else:
		if decrypt:
			try:
				data = decode(key, (
					(await main_collection.find_one({"_id": src}))['data'].decode("utf-8"))
				)
				print(data)
			except AttributeError:
				data = decode(key, (await main_collection.find_one({"_id": src}))['data'])
			except TypeError:
				await main_collection.insert_one(
					{
						"_id": src,
						"data": encode(key, str({}))
					}
				)
				data = {}
			if lEval:
				value = ast.literal_eval(str(data))
			else:
				value = str(data)
			cache.cache(src, value)
			return value
		else:
			try:
				data = (await main_collection.find_one({"_id": src}))['data']
			except TypeError:
				await main_collection.insert_one({"_id": src, "data": str({})})
				data = {}
			if lEval:
				value = ast.literal_eval(data)
			else:
				value = str(data)
			cache.cache(src, value)
			return value


async def write(src, data, encrypt=True):
	cache.cache(src, data)
	if encrypt:
		data = encode(key, str(data))
		try:
			await main_collection.insert_one({"_id": src, "data": str(data)})
		except:
			await main_collection.update_one(
				{"_id": src},
				{"$set": {"data": str(data)}}
			)
	else:
		try:
			await main_collection.insert_one({"_id": src, "data": str(data)})
		except:
			await main_collection.update_one(
				{"_id": src},
				{"$set": {"data": str(data)}}
			)
