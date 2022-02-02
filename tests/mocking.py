from unittest.mock import Mock


class Database:

    def unchanged(self):
        return "this method is unchanged"

    def insert(self):
        return "the real method"


#
# Original, un-mocked
#
d = Database()
print(f"1a: {d.unchanged()}")
print(f"1b: {d.insert()}")

# #
# # Mocking using "return_value"
# #
# d.insert = Mock(return_value="i am the MOCK method")
# print(f"2a: {d.unchanged()}")
# print(f"2b: {d.insert()}")

# #
# # Mocking using side_effect
# #
# d.insert = Mock(side_effect=KeyError)
# print(f"3a: {d.unchanged()}")
# print(f"3b: {d.insert()}")
