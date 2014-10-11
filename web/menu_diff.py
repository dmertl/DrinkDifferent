from models import Beverage


def diff_beverages(old_beverages, new_beverages):
    """
    Return the difference in beverages between an old list and a new list.

    :param old_beverages: Old beverage list.
    :type old_beverages: Beverage[]
    :param new_beverages: New beverage list.
    :type new_beverages: Beverage[]
    :return: List of added, removed Beverages
    :rtype: Beverage[], Beverage[]
    """
    added = []
    removed = []
    for old_beverage in old_beverages:
        found = False
        for new_beverage in new_beverages:
            if new_beverage.name == old_beverage.name and new_beverage.brewery == old_beverage.brewery:
                found = True
                break
        if not found:
            # Old beverage was removed
            removed.append(old_beverage)
    for new_beverage in new_beverages:
        found = False
        for old_beverage in old_beverages:
            if old_beverage.name == new_beverage.name and old_beverage.brewery == new_beverage.brewery:
                found = True
                break
        if not found:
            # New beverage was added
            added.append(new_beverage)
    return added, removed
