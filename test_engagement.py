import pytest
from engagement_engine import EngagementEngine
 
 
# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
 
@pytest.fixture
def basic_user():
    return EngagementEngine("user_basic")
 
 
@pytest.fixture
def verified_user():
    return EngagementEngine("user_verified", verified=True)
 
 
# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------
 
class TestInit:
    def test_default_score_is_zero(self, basic_user):
        assert basic_user.score == 0.0
 
    def test_handle_stored(self, basic_user):
        assert basic_user.user_handle == "user_basic"
 
    def test_verified_false_by_default(self, basic_user):
        assert basic_user.verified is False
 
    def test_verified_true_when_set(self, verified_user):
        assert verified_user.verified is True
 
 
# ---------------------------------------------------------------------------
# process_interaction
# ---------------------------------------------------------------------------
 
class TestProcessInteraction:
    # --- valid interaction types ---
 
    def test_like_adds_correct_points(self, basic_user):
        basic_user.process_interaction("like", 10)
        assert basic_user.score == 10.0  # 1 * 10
 
    def test_comment_adds_correct_points(self, basic_user):
        basic_user.process_interaction("comment", 4)
        assert basic_user.score == 20.0  # 5 * 4
 
    def test_share_adds_correct_points(self, basic_user):
        basic_user.process_interaction("share", 3)
        assert basic_user.score == 30.0  # 10 * 3
 
    def test_valid_interaction_returns_true(self, basic_user):
        assert basic_user.process_interaction("like") is True
 
    # --- default count ---
 
    def test_default_count_is_one(self, basic_user):
        basic_user.process_interaction("share")
        assert basic_user.score == 10.0
 
    # --- verified multiplier ---
 
    def test_verified_user_gets_1_5x_multiplier(self, verified_user):
        verified_user.process_interaction("like", 10)
        assert verified_user.score == pytest.approx(15.0)  # 1 * 10 * 1.5
 
    def test_verified_comment_multiplier(self, verified_user):
        verified_user.process_interaction("comment", 2)
        assert verified_user.score == pytest.approx(15.0)  # 5 * 2 * 1.5
 
    def test_verified_share_multiplier(self, verified_user):
        verified_user.process_interaction("share", 2)
        assert verified_user.score == pytest.approx(30.0)  # 10 * 2 * 1.5
 
    # --- invalid type ---
 
    def test_unknown_type_returns_false(self, basic_user):
        assert basic_user.process_interaction("retweet") is False
 
    def test_unknown_type_does_not_change_score(self, basic_user):
        basic_user.process_interaction("retweet", 100)
        assert basic_user.score == 0.0
 
    # --- negative count ---
 
    def test_negative_count_raises_value_error(self, basic_user):
        with pytest.raises(ValueError, match="Negative count"):
            basic_user.process_interaction("like", -1)
 
    # --- zero count ---
 
    def test_zero_count_adds_no_points(self, basic_user):
        basic_user.process_interaction("like", 0)
        assert basic_user.score == 0.0
 
    # --- cumulative interactions ---
 
    def test_score_accumulates_across_calls(self, basic_user):
        basic_user.process_interaction("like", 10)   # +10
        basic_user.process_interaction("comment", 2) # +10
        basic_user.process_interaction("share", 1)   # +10
        assert basic_user.score == 30.0
 
 
# ---------------------------------------------------------------------------
# get_tier
# ---------------------------------------------------------------------------
 
class TestGetTier:
    def test_newbie_at_zero(self, basic_user):
        assert basic_user.get_tier() == "Newbie"
 
    def test_newbie_just_below_100(self, basic_user):
        basic_user.score = 99.9
        assert basic_user.get_tier() == "Newbie"
 
    def test_influencer_at_exactly_100(self, basic_user):
        basic_user.score = 100
        assert basic_user.get_tier() == "Influencer"
 
    def test_influencer_at_500(self, basic_user):
        basic_user.score = 500
        assert basic_user.get_tier() == "Influencer"
 
    def test_influencer_at_exactly_1000(self, basic_user):
        basic_user.score = 1000
        assert basic_user.get_tier() == "Influencer"
 
    def test_icon_just_above_1000(self, basic_user):
        basic_user.score = 1000.1
        assert basic_user.get_tier() == "Icon"
 
    def test_icon_at_large_score(self, basic_user):
        basic_user.score = 999999
        assert basic_user.get_tier() == "Icon"
 
 
# ---------------------------------------------------------------------------
# apply_penalty
# ---------------------------------------------------------------------------
 
class TestApplyPenalty:
    def test_penalty_reduces_score(self, basic_user):
        basic_user.score = 100.0
        basic_user.apply_penalty(1)           # 20% of 100 = 20
        assert basic_user.score == pytest.approx(80.0)
 
    def test_penalty_with_two_reports(self, basic_user):
        basic_user.score = 100.0
        basic_user.apply_penalty(2)           # 40% of 100 = 40
        assert basic_user.score == pytest.approx(60.0)
 
    def test_score_does_not_go_below_zero(self, basic_user):
        basic_user.score = 10.0
        basic_user.apply_penalty(10)          # 200% reduction → clamped at 0
        assert basic_user.score == 0.0
 
    def test_zero_reports_no_score_change(self, basic_user):
        basic_user.score = 100.0
        basic_user.apply_penalty(0)
        assert basic_user.score == pytest.approx(100.0)
 
    def test_more_than_10_reports_revokes_verified(self):
        engine = EngagementEngine("star", verified=True)
        engine.score = 500.0
        engine.apply_penalty(11)
        assert engine.verified is False
 
    def test_exactly_10_reports_keeps_verified(self):
        engine = EngagementEngine("star", verified=True)
        engine.score = 500.0
        engine.apply_penalty(10)
        assert engine.verified is True   # threshold is > 10, not >= 10
 
    def test_penalty_on_zero_score_stays_zero(self, basic_user):
        basic_user.apply_penalty(5)
        assert basic_user.score == 0.0
 
    def test_penalty_applied_to_verified_user_score(self):
        engine = EngagementEngine("v", verified=True)
        engine.score = 200.0
        engine.apply_penalty(3)           # 60% of 200 = 120 → score = 80
        assert engine.score == pytest.approx(80.0)