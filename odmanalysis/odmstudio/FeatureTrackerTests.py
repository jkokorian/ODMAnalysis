import unittest
from odmstudio_lib import FeatureTracker,CurveFitTracker,FFTPhaseShiftTracker



class Test_FeatureTrackerTests(unittest.TestCase):
    def test_TrackerRegistrations(self):

        featureTrackers= FeatureTracker.getRegisteredFeatureTrackers()
        self.assertTrue(len(featureTrackers) > 0)

    def test_TrackerRetreival(self):
        featureTrackers = FeatureTracker.getRegisteredFeatureTrackers()

        tracker = featureTrackers[0]
        print tracker
        self.assertTrue(tracker is CurveFitTracker)

    def test_DefaultDisplayName(self):
        displayName = FeatureTracker.getDisplayName()
        self.assertTrue(displayName is not None)

    def test_CustomDisplayName(self):
        self.assertTrue(CurveFitTracker.getDisplayName() == "Curve-fit")


if __name__ == '__main__':
    unittest.main()
