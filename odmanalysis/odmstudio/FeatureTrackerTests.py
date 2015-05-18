import unittest
import odmstudio_framework as fw
from odmstudio_lib import FeatureTracker


class Test_FeatureTrackerTests(unittest.TestCase):
    def test_TrackerRegistrations(self):
        fw.loadPlugins()

        featureTrackers= fw.FeatureTrackerFactory.getFeatureTrackers()
        self.assertTrue(len(featureTrackers) > 0)

    def test_TrackerRetreival(self):
        fw.loadPlugins()

        featureTrackers= fw.FeatureTrackerFactory.getFeatureTrackers()


        tracker = featureTrackers[0]
        print tracker
        self.assertTrue(tracker is CurveFitTracker)

    def test_DefaultDisplayName(self):
        displayName = FeatureTracker.getDisplayName()
        self.assertTrue(displayName is not None)

    


if __name__ == '__main__':
    unittest.main()
