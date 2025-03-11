import csv
from operator import attrgetter


class Analyser:
    def __init__(self, filename):
        self.data = []
        self.load_csv(filename)

    def load_csv(self, filename):
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.data.append(type('DataObject', (), row))

    def sort_by(self, attribute, reverse=False):
        return sorted(self.data, key=attrgetter(attribute), reverse=reverse)

    @staticmethod
    def filter(data, condition):
        return [obj for obj in data if condition(obj)]

    def query(self, attribute, value):
        return [obj for obj in self.data if getattr(obj, attribute) == value]

    def analyse_list(self):
        self.find_free_accounts()
        self.find_paid()
        self.find_free()
        self.find_lapsed_activesubs()
        self.find_not_tagged_with_fetish()

        return


    def find_free_accounts(self):
        """
        Finds accounts which are free but not currently subscribed to.
        Will highlight both free trials and free accounts who are not subscribed.
        """
        data = self.query(attribute='price', value='0') # no price to subscribe
        data = self.filter(data, lambda x: x.subscription_status == 'NO_SUBSCRIPTION') # not currently subscribed to
        data = self.filter(data, lambda x: 'free' not in x.lists) # not in the 'free' list
        data = self.filter(data, lambda x: 'inactive' not in x.lists)

        for obj in data:
            print(f"free trial/account found: https://onlyfans.com/{obj.username}")

        return data

    def find_paid(self):
        """
        Finds accounts which have a cost, but are not in the paid list.
        """
        data = self.filter(self.data, lambda x: 'paid' not in x.lists)
        data = self.filter(data, lambda x: x.price != '0')
        data = self.filter(data, lambda x: 'inactive' not in x.lists)

        for obj in data:
            print(f"not flagged as paid: https://onlyfans.com/{obj.username} (lists: {obj.lists})")

        return data

    def find_free(self):
        """
        Finds accounts which are free, but are not in the free list.
        Ignores active subs, free trials and inactive accounts.
        """

        data = self.filter(self.data, lambda x: 'free' not in x.lists)
        data = self.filter(data, lambda x: x.price == '0')

        data = self.filter(data, lambda x: 'activesub' not in x.lists)
        data = self.filter(data, lambda x: 'freetrial' not in x.lists)
        data = self.filter(data, lambda x: 'inactive' not in x.lists)

        for obj in data:
            print(f"not flagged as free: https://onlyfans.com/{obj.username} (lists: {obj.lists})")

        return data


    def find_lapsed_activesubs(self):
        """
        finds accounts which are in the activesub list, but have not got an active subscription.
        """
        data = self.filter(self.data, lambda x: 'activesub' in x.lists)
        data = self.filter(data, lambda x: x.subscription_status == 'NO_SUBSCRIPTION') # not currently subscribed to

        for obj in data:
            print(f"lapsed activesub: https://onlyfans.com/{obj.username}")

        return data

    def find_not_tagged_with_fetish(self):
        """
        finds accounts which are not tagged with a relevant fetish.

        """

        data = self.filter(self.data, lambda x: 'femdom' not in x.lists)
        data = self.filter(data, lambda x: 'vanilla' not in x.lists)
        data = self.filter(data, lambda x: 'femboy' not in x.lists)
        data = self.filter(data, lambda x: 'femboy' not in x.lists)
        data = self.filter(data, lambda x: 'qos' not in x.lists)
        data = self.filter(data, lambda x: 'male' not in x.lists)

        data = self.filter(data, lambda x: 'inactive' not in x.lists)


        for obj in data:
            print(f"not tagged with a fetish: https://onlyfans.com/{obj.username} (lists: {obj.lists})")

