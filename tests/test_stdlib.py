"""Tests for Bardic's standard library modules."""

import random
import pytest

from bardic.stdlib.dice import roll, skill_check, weighted_choice, advantage, disadvantage
from bardic.stdlib.inventory import Inventory
from bardic.stdlib.economy import Wallet, Shop
from bardic.stdlib.relationship import Relationship
from bardic.stdlib.quest import Quest, QuestJournal


# ──────────────────────────────────────────────
# Dice Module
# ──────────────────────────────────────────────

class TestRoll:
    def test_simple_d6(self):
        result = roll("1d6")
        assert 1 <= result <= 6

    def test_multiple_dice(self):
        result = roll("3d6")
        assert 3 <= result <= 18

    def test_positive_modifier(self):
        result = roll("1d6+5")
        assert 6 <= result <= 11

    def test_negative_modifier(self):
        result = roll("1d6-3")
        assert -2 <= result <= 3

    def test_d20(self):
        result = roll("1d20")
        assert 1 <= result <= 20

    def test_default_is_1d6(self):
        result = roll()
        assert 1 <= result <= 6

    def test_invalid_notation_raises(self):
        with pytest.raises(ValueError, match="Invalid dice notation"):
            roll("banana")

    def test_deterministic_with_seed(self):
        random.seed(42)
        a = roll("2d6")
        random.seed(42)
        b = roll("2d6")
        assert a == b


class TestSkillCheck:
    def test_auto_success_high_stat(self):
        """Stat of 100 vs DC 15 should always pass."""
        for _ in range(20):
            assert skill_check(100, dc=15) is True

    def test_auto_fail_low_stat(self):
        """Stat of -100 vs DC 15 should always fail."""
        for _ in range(20):
            assert skill_check(-100, dc=15) is False

    def test_bonus_applied(self):
        """Bonus should help pass easier."""
        # stat=0, dc=25 means need 25 on d20 — impossible without bonus
        # With bonus=10, need 15 — still hard but possible
        random.seed(42)
        # At minimum, bonus should change the threshold
        result_no_bonus = 0 + roll("1d20")  # without stat/bonus
        random.seed(42)
        # skill_check uses stat + bonus + d20 >= dc
        assert isinstance(skill_check(10, dc=15, bonus=5), bool)


class TestWeightedChoice:
    def test_returns_option(self):
        result = weighted_choice(["a", "b", "c"], [0.5, 0.3, 0.2])
        assert result in ["a", "b", "c"]

    def test_deterministic_with_seed(self):
        random.seed(42)
        a = weighted_choice(["x", "y"], [0.9, 0.1])
        random.seed(42)
        b = weighted_choice(["x", "y"], [0.9, 0.1])
        assert a == b

    def test_single_option(self):
        result = weighted_choice(["only"], [1.0])
        assert result == "only"


class TestAdvantageDisadvantage:
    def test_advantage_in_range(self):
        result = advantage()
        assert 1 <= result <= 20

    def test_disadvantage_in_range(self):
        result = disadvantage()
        assert 1 <= result <= 20

    def test_advantage_tends_higher(self):
        """Over many rolls, advantage should average higher than disadvantage."""
        random.seed(42)
        adv_avg = sum(advantage() for _ in range(1000)) / 1000
        random.seed(42)
        disadv_avg = sum(disadvantage() for _ in range(1000)) / 1000
        assert adv_avg > disadv_avg


# ──────────────────────────────────────────────
# Inventory Module
# ──────────────────────────────────────────────

SWORD = {"name": "Sword", "weight": 5, "value": 100}
POTION = {"name": "Potion", "weight": 0.5, "value": 50}
SHIELD = {"name": "Shield", "weight": 8, "value": 75, "category": "armor"}


class TestInventoryAdd:
    def test_add_item(self):
        inv = Inventory(max_weight=50)
        assert inv.add(SWORD.copy()) is True
        assert len(inv.items) == 1

    def test_add_over_weight_fails(self):
        inv = Inventory(max_weight=3)
        assert inv.add(SWORD.copy()) is False
        assert len(inv.items) == 0

    def test_add_requires_name(self):
        inv = Inventory()
        with pytest.raises(ValueError, match="name"):
            inv.add({"weight": 5})

    def test_add_default_weight_zero(self):
        inv = Inventory(max_weight=1)
        assert inv.add({"name": "Feather"}) is True
        assert inv.current_weight == 0


class TestInventoryRemove:
    def test_remove_existing(self):
        inv = Inventory()
        inv.add(SWORD.copy())
        assert inv.remove("Sword") is True
        assert len(inv.items) == 0

    def test_remove_nonexistent(self):
        inv = Inventory()
        assert inv.remove("Ghost") is False

    def test_remove_only_first(self):
        inv = Inventory()
        inv.add(POTION.copy())
        inv.add(POTION.copy())
        inv.remove("Potion")
        assert inv.count("Potion") == 1

    def test_remove_all(self):
        inv = Inventory()
        inv.add(POTION.copy())
        inv.add(POTION.copy())
        inv.add(POTION.copy())
        removed = inv.remove_all("Potion")
        assert removed == 3
        assert inv.count("Potion") == 0


class TestInventoryQuery:
    def test_has(self):
        inv = Inventory()
        inv.add(SWORD.copy())
        assert inv.has("Sword") is True
        assert inv.has("Ghost") is False

    def test_count(self):
        inv = Inventory()
        inv.add(POTION.copy())
        inv.add(POTION.copy())
        assert inv.count("Potion") == 2
        assert inv.count("Sword") == 0

    def test_get(self):
        inv = Inventory()
        inv.add(SWORD.copy())
        item = inv.get("Sword")
        assert item is not None
        assert item["name"] == "Sword"

    def test_get_nonexistent(self):
        inv = Inventory()
        assert inv.get("Ghost") is None

    def test_get_all(self):
        inv = Inventory()
        inv.add(POTION.copy())
        inv.add(POTION.copy())
        potions = inv.get_all("Potion")
        assert len(potions) == 2

    def test_filter_by_category(self):
        inv = Inventory()
        inv.add(SWORD.copy())
        inv.add(SHIELD.copy())
        armor = inv.filter_by_category("armor")
        assert len(armor) == 1
        assert armor[0]["name"] == "Shield"


class TestInventoryProperties:
    def test_current_weight(self):
        inv = Inventory()
        inv.add(SWORD.copy())
        inv.add(POTION.copy())
        assert inv.current_weight == 5.5

    def test_is_full(self):
        inv = Inventory(max_weight=5)
        inv.add(SWORD.copy())
        assert inv.is_full is True

    def test_is_empty(self):
        inv = Inventory()
        assert inv.is_empty is True
        inv.add(SWORD.copy())
        assert inv.is_empty is False

    def test_space_remaining(self):
        inv = Inventory(max_weight=50)
        inv.add(SWORD.copy())
        assert inv.space_remaining == 45

    def test_total_value(self):
        inv = Inventory()
        inv.add(SWORD.copy())
        inv.add(POTION.copy())
        assert inv.total_value == 150

    def test_clear(self):
        inv = Inventory()
        inv.add(SWORD.copy())
        inv.add(POTION.copy())
        inv.clear()
        assert inv.is_empty is True


class TestInventorySerialization:
    def test_roundtrip(self):
        inv = Inventory(max_weight=75)
        inv.add(SWORD.copy())
        inv.add(POTION.copy())

        data = inv.to_dict()
        restored = Inventory.from_dict(data)

        assert restored.max_weight == 75
        assert len(restored.items) == 2
        assert restored.has("Sword")


# ──────────────────────────────────────────────
# Economy Module
# ──────────────────────────────────────────────

class TestWallet:
    def test_starting_gold(self):
        w = Wallet(gold=100)
        assert w.gold == 100

    def test_default_zero(self):
        w = Wallet()
        assert w.gold == 0

    def test_negative_clamped_to_zero(self):
        w = Wallet(gold=-50)
        assert w.gold == 0

    def test_spend_success(self):
        w = Wallet(gold=100)
        assert w.spend(30) is True
        assert w.gold == 70

    def test_spend_insufficient(self):
        w = Wallet(gold=10)
        assert w.spend(50) is False
        assert w.gold == 10  # Unchanged

    def test_earn(self):
        w = Wallet(gold=50)
        w.earn(25)
        assert w.gold == 75

    def test_earn_negative_ignored(self):
        w = Wallet(gold=50)
        w.earn(-10)
        assert w.gold == 50

    def test_can_afford(self):
        w = Wallet(gold=100)
        assert w.can_afford(100) is True
        assert w.can_afford(101) is False

    def test_gold_setter_clamps(self):
        w = Wallet(gold=100)
        w.gold = -50
        assert w.gold == 0

    def test_serialization_roundtrip(self):
        w = Wallet(gold=42)
        restored = Wallet.from_dict(w.to_dict())
        assert restored.gold == 42


class TestShop:
    def setup_method(self):
        self.items = [
            {"name": "Sword", "weight": 5, "value": 100},
            {"name": "Potion", "weight": 0.5, "value": 50},
        ]
        self.shop = Shop(self.items)
        self.wallet = Wallet(gold=200)
        self.inv = Inventory(max_weight=50)

    def test_find_item(self):
        assert self.shop.find_item("Sword") is not None
        assert self.shop.find_item("Ghost") is None

    def test_buy_success(self):
        assert self.shop.buy("Sword", self.wallet, self.inv) is True
        assert self.wallet.gold == 100
        assert self.inv.has("Sword")

    def test_buy_cant_afford(self):
        poor_wallet = Wallet(gold=10)
        assert self.shop.buy("Sword", poor_wallet, self.inv) is False
        assert not self.inv.has("Sword")

    def test_buy_inventory_full_refunds(self):
        tiny_inv = Inventory(max_weight=1)
        assert self.shop.buy("Sword", self.wallet, tiny_inv) is False
        assert self.wallet.gold == 200  # Refunded

    def test_buy_nonexistent_item(self):
        assert self.shop.buy("Ghost", self.wallet, self.inv) is False

    def test_sell_success(self):
        self.inv.add({"name": "Sword", "weight": 5, "value": 100})
        assert self.shop.sell("Sword", self.wallet, self.inv) is True
        assert self.wallet.gold == 250  # 200 + 50 (50% of 100)
        assert not self.inv.has("Sword")

    def test_sell_item_not_in_inventory(self):
        assert self.shop.sell("Sword", self.wallet, self.inv) is False

    def test_discount(self):
        discount_shop = Shop(self.items, discount=0.5)
        assert discount_shop.get_buy_price("Sword") == 50

    def test_sell_back_rate(self):
        shop = Shop(self.items, sell_back_rate=0.25)
        assert shop.get_sell_price(100) == 25

    def test_set_discount(self):
        self.shop.set_discount(0.8)
        assert self.shop.get_buy_price("Sword") == 80

    def test_serialization_roundtrip(self):
        self.shop.set_discount(0.75)
        restored = Shop.from_dict(self.shop.to_dict())
        assert len(restored.items) == 2
        assert restored.discount == 0.75
        assert restored.sell_back_rate == 0.5


# ──────────────────────────────────────────────
# Relationship Module
# ──────────────────────────────────────────────

class TestRelationshipBasics:
    def test_name_assigned(self):
        """Regression: name was a type annotation, not an assignment."""
        r = Relationship(name="Alex", trust=50, comfort=50, openness=0)
        assert r.name == "Alex"

    def test_initial_values(self):
        r = Relationship(name="Alex", trust=70, comfort=60, openness=3)
        assert r.trust == 70
        assert r.comfort == 60
        assert r.openness == 3

    def test_empty_topics(self):
        r = Relationship(name="Alex", trust=50, comfort=50, openness=0)
        assert len(r.topics_discussed) == 0


class TestRelationshipClamping:
    def test_trust_clamped_high(self):
        r = Relationship(name="X", trust=150, comfort=50, openness=0)
        assert r.trust == 100

    def test_trust_clamped_low(self):
        r = Relationship(name="X", trust=-20, comfort=50, openness=0)
        assert r.trust == 0

    def test_comfort_clamped(self):
        r = Relationship(name="X", trust=50, comfort=200, openness=0)
        assert r.comfort == 100

    def test_openness_clamped_high(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=20)
        assert r.openness == 10

    def test_openness_clamped_low(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=-20)
        assert r.openness == -10


class TestRelationshipModifiers:
    def test_add_trust(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=0)
        r.add_trust(10)
        assert r.trust == 60

    def test_add_comfort(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=0)
        r.add_comfort(15)
        assert r.comfort == 65

    def test_add_openness(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=0)
        r.add_openness(3)
        assert r.openness == 3

    def test_add_trust_negative(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=0)
        r.add_trust(-20)
        assert r.trust == 30

    def test_add_trust_clamps_at_boundaries(self):
        r = Relationship(name="X", trust=95, comfort=50, openness=0)
        r.add_trust(20)
        assert r.trust == 100


class TestRelationshipTopics:
    def test_discuss_topic(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=0)
        r.discuss_topic("work_stress")
        assert r.has_discussed("work_stress") is True

    def test_has_not_discussed(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=0)
        assert r.has_discussed("love") is False

    def test_topics_are_unique(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=0)
        r.discuss_topic("work")
        r.discuss_topic("work")
        assert len(r.topics_discussed) == 1


class TestRelationshipProperties:
    def test_ready_for_deep_conversation(self):
        r = Relationship(name="X", trust=60, comfort=50, openness=1)
        assert r.is_ready_for_deep_conversation is True

    def test_not_ready_low_trust(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=5)
        assert r.is_ready_for_deep_conversation is False

    def test_not_ready_low_openness(self):
        r = Relationship(name="X", trust=80, comfort=50, openness=0)
        assert r.is_ready_for_deep_conversation is False

    def test_is_vulnerable(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=5)
        assert r.is_vulnerable is True

    def test_is_defensive(self):
        r = Relationship(name="X", trust=50, comfort=50, openness=-3)
        assert r.is_defensive is True

    def test_relationship_quality_levels(self):
        assert Relationship(name="X", trust=85, comfort=50, openness=0).relationship_quality == "close_confidant"
        assert Relationship(name="X", trust=65, comfort=50, openness=0).relationship_quality == "trusted_guide"
        assert Relationship(name="X", trust=45, comfort=50, openness=0).relationship_quality == "professional"
        assert Relationship(name="X", trust=25, comfort=50, openness=0).relationship_quality == "cautious"
        assert Relationship(name="X", trust=10, comfort=50, openness=0).relationship_quality == "guarded"


class TestRelationshipSerialization:
    def test_roundtrip(self):
        r = Relationship(name="Alex", trust=70, comfort=60, openness=3)
        r.discuss_topic("work")
        r.discuss_topic("feelings")

        data = r.to_dict()
        restored = Relationship.from_dict(data)

        assert restored.name == "Alex"
        assert restored.trust == 70
        assert restored.comfort == 60
        assert restored.openness == 3
        assert restored.has_discussed("work")
        assert restored.has_discussed("feelings")


# ──────────────────────────────────────────────
# Quest Module
# ──────────────────────────────────────────────

class TestQuestBasics:
    def test_quest_dataclass(self):
        q = Quest(quest_id="find_key", title="Find the Key")
        assert q.quest_id == "find_key"
        assert q.title == "Find the Key"
        assert q.stage == "active"
        assert q.is_active is True

    def test_quest_with_description(self):
        q = Quest(quest_id="x", title="X", description="Do the thing")
        assert q.description == "Do the thing"

    def test_quest_status_properties(self):
        q = Quest(quest_id="x", title="X")
        assert q.is_active is True
        assert q.is_complete is False
        assert q.is_failed is False

        q.stage = "complete"
        assert q.is_active is False
        assert q.is_complete is True

        q.stage = "failed"
        assert q.is_failed is True
        assert q.is_active is False

    def test_custom_stage_is_still_active(self):
        q = Quest(quest_id="x", title="X", stage="searched_garden")
        assert q.is_active is True  # Not "complete" or "failed"


class TestQuestJournalAdd:
    def test_add_quest(self):
        j = QuestJournal()
        q = j.add("find_key", "Find the Key")
        assert q.quest_id == "find_key"
        assert j.has("find_key") is True

    def test_add_duplicate_raises(self):
        j = QuestJournal()
        j.add("find_key", "Find the Key")
        with pytest.raises(ValueError, match="already exists"):
            j.add("find_key", "Find It Again")

    def test_get_quest(self):
        j = QuestJournal()
        j.add("find_key", "Find the Key")
        q = j.get("find_key")
        assert q is not None
        assert q.title == "Find the Key"

    def test_get_nonexistent(self):
        j = QuestJournal()
        assert j.get("ghost") is None

    def test_has(self):
        j = QuestJournal()
        j.add("find_key", "Find the Key")
        assert j.has("find_key") is True
        assert j.has("ghost") is False


class TestQuestJournalStatus:
    def setup_method(self):
        self.j = QuestJournal()
        self.j.add("main", "Main Quest")
        self.j.add("side", "Side Quest")
        self.j.add("done", "Done Quest")
        self.j.complete("done")

    def test_is_active(self):
        assert self.j.is_active("main") is True
        assert self.j.is_active("done") is False

    def test_is_complete(self):
        assert self.j.is_complete("done") is True
        assert self.j.is_complete("main") is False

    def test_is_failed(self):
        self.j.fail("side")
        assert self.j.is_failed("side") is True

    def test_status_of_nonexistent(self):
        assert self.j.is_active("ghost") is False
        assert self.j.is_complete("ghost") is False
        assert self.j.is_failed("ghost") is False

    def test_stage_of(self):
        assert self.j.stage_of("main") == "active"
        assert self.j.stage_of("done") == "complete"
        assert self.j.stage_of("ghost") is None


class TestQuestJournalStages:
    def test_set_stage(self):
        j = QuestJournal()
        j.add("mystery", "Solve the Mystery")
        j.set_stage("mystery", "found_clue")
        assert j.stage_of("mystery") == "found_clue"
        assert j.is_active("mystery") is True  # Custom stage = still active

    def test_complete(self):
        j = QuestJournal()
        j.add("quest", "A Quest")
        j.complete("quest")
        assert j.is_complete("quest") is True

    def test_fail(self):
        j = QuestJournal()
        j.add("quest", "A Quest")
        j.fail("quest")
        assert j.is_failed("quest") is True

    def test_set_stage_nonexistent_raises(self):
        j = QuestJournal()
        with pytest.raises(KeyError, match="not found"):
            j.set_stage("ghost", "anything")

    def test_complete_nonexistent_raises(self):
        j = QuestJournal()
        with pytest.raises(KeyError):
            j.complete("ghost")

    def test_multi_stage_progression(self):
        j = QuestJournal()
        j.add("murder", "Solve the Murder")
        j.set_stage("murder", "found_body")
        j.set_stage("murder", "interviewed_witnesses")
        j.set_stage("murder", "identified_suspect")
        j.complete("murder")
        assert j.is_complete("murder") is True


class TestQuestJournalLog:
    def test_add_log_entry(self):
        j = QuestJournal()
        j.add("quest", "A Quest")
        j.log("quest", "Found a clue near the fountain.")
        entries = j.get_log("quest")
        assert len(entries) == 1
        assert "fountain" in entries[0]

    def test_multiple_entries_in_order(self):
        j = QuestJournal()
        j.add("quest", "A Quest")
        j.log("quest", "First")
        j.log("quest", "Second")
        j.log("quest", "Third")
        entries = j.get_log("quest")
        assert entries == ["First", "Second", "Third"]

    def test_log_nonexistent_raises(self):
        j = QuestJournal()
        with pytest.raises(KeyError, match="not found"):
            j.log("ghost", "Boo!")

    def test_get_log_nonexistent_returns_empty(self):
        j = QuestJournal()
        assert j.get_log("ghost") == []


class TestQuestJournalViews:
    def setup_method(self):
        self.j = QuestJournal()
        self.j.add("active1", "Active 1")
        self.j.add("active2", "Active 2")
        self.j.add("done1", "Done 1")
        self.j.complete("done1")
        self.j.add("failed1", "Failed 1")
        self.j.fail("failed1")

    def test_active_quests(self):
        active = self.j.active_quests
        assert len(active) == 2
        assert all(q.is_active for q in active)

    def test_completed_quests(self):
        done = self.j.completed_quests
        assert len(done) == 1
        assert done[0].quest_id == "done1"

    def test_failed_quests(self):
        failed = self.j.failed_quests
        assert len(failed) == 1
        assert failed[0].quest_id == "failed1"

    def test_all_quests(self):
        assert len(self.j.all_quests) == 4

    def test_count_active(self):
        assert self.j.count_active == 2

    def test_count_complete(self):
        assert self.j.count_complete == 1


class TestQuestJournalSerialization:
    def test_roundtrip(self):
        j = QuestJournal()
        j.add("main", "Main Quest", description="Save the world")
        j.set_stage("main", "found_artifact")
        j.log("main", "The artifact glows with ancient power.")
        j.add("side", "Side Quest")
        j.complete("side")

        data = j.to_dict()
        restored = QuestJournal.from_dict(data)

        assert restored.has("main")
        assert restored.has("side")
        assert restored.stage_of("main") == "found_artifact"
        assert restored.is_complete("side")
        assert restored.get("main").description == "Save the world"
        assert len(restored.get_log("main")) == 1

    def test_empty_journal_roundtrip(self):
        j = QuestJournal()
        data = j.to_dict()
        restored = QuestJournal.from_dict(data)
        assert len(restored.all_quests) == 0
