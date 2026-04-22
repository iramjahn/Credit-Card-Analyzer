# categories.py

class Category:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    
    def __repr__(self):
        return f"Category({self.name})"


# Create individual category objects
dining = Category('dining', 'Dining & Restaurants')
groceries = Category('groceries', 'Groceries')
travel = Category('travel', 'Travel & Hotels')
gas = Category('gas', 'Gas Stations')
drugstores = Category('drugstores', 'Drugstores')
entertainment = Category('entertainment', 'Entertainment')
shopping = Category('shopping', 'Shopping')
default = Category('default', 'Other/General')

# Put them all in a list
CATEGORIES = [
    dining,
    groceries,
    travel,
    gas,
    drugstores,
    entertainment,
    shopping,
    default
]


