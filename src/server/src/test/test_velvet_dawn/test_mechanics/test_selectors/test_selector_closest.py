import velvet_dawn.units
from velvet_dawn.dao import app
from test.base_test import BaseTest
from velvet_dawn.mechanics import selectors
from velvet_dawn.models.coordinate import Coordinate


class TestSelectorsClosest(BaseTest):

    def test_selector_parsing(self):
        selector_closest_unit = selectors.get_selector("0", "closest")
        selector_closest_enemy = selectors.get_selector("0", "closest-enemy")
        selector_closest_friendly = selectors.get_selector("0", "closest-friendly")

        self.assertTrue(isinstance(selector_closest_unit, selectors.SelectorClosest))
        self.assertTrue(isinstance(selector_closest_enemy, selectors.SelectorClosestEnemy))
        self.assertTrue(isinstance(selector_closest_friendly, selectors.SelectorClosestFriendly))

    def test_selector_unit(self):
        with app.app_context():
            self.prepare_game()

            unit = velvet_dawn.db.units.get_units_at_positions(Coordinate(5, 0))[0]

            selector_closest_unit = selectors.get_selector("0", "closest")
            selector_closest_enemy = selectors.get_selector("0", "closest-enemy")
            selector_closest_friendly = selectors.get_selector("0", "closest-friendly")

            closest_unit = selector_closest_unit.get_selection(unit)
            closest_enemy = selector_closest_enemy.get_selection(unit)
            closest_friendly = selector_closest_friendly.get_selection(unit)

            self.assertEqual(1, len(closest_unit))
            self.assertEqual(1, len(closest_enemy))
            self.assertEqual(1, len(closest_friendly))

            # Test that self is excluded
            self.assertNotEqual(closest_unit[0].id, unit.id)
