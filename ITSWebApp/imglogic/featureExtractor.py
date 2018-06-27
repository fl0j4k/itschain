import cv2
import numpy as np
import math
import pickle


class ImageEngine:

    # **
    # Extract features of a certain image
    # **
    def featureExtractor(self, imgpath, filename):
        img_inp = cv2.imread(imgpath + '/' + filename)
        height1, width1, channels1 = img_inp.shape
        lum_img_inp = cv2.cvtColor(img_inp, cv2.COLOR_BGR2LAB)
        lum, a, b = cv2.split(lum_img_inp)
        lum_vals = np.array(lum)

        #  =========== calculate coefficients ===========
        # for description see documentation
        DISTANCE_COEFF = 0.50
        COMP_COEFF = 0.1
        SPLIT_COEFF = 4

        width_1_new = width1 // SPLIT_COEFF
        height_1_new = height1 // SPLIT_COEFF

        multiplicator_row = 0
        multiplicator_col = -1
        hitcount = 0

        allFeatures = {}
        imginfo = {}
        imginfo[0] = np.mean(lum_vals)
        imginfo[1] = width1
        imginfo[2] = height1
        allFeatures[0] = imginfo
        for i in range(SPLIT_COEFF ** 2):
            if (i % SPLIT_COEFF == 0):
                multiplicator_row = 0
                multiplicator_col += 1

            # split both images
            prt1 = img_inp[height_1_new * multiplicator_row:height_1_new * (multiplicator_row + 1),
                   width_1_new * multiplicator_col:width_1_new * (multiplicator_col + 1)]
            multiplicator_row += 1;

            # ORB Algorithm (efficient alternative to SIFT)
            # Keypoint and descriptor extraction
            orb = cv2.ORB_create(50, 1.2, nlevels=8, edgeThreshold=5)

            gray_img_inp = cv2.cvtColor(prt1, cv2.COLOR_BGR2GRAY)
            kp_img_inp, des_img_inp = orb.detectAndCompute(gray_img_inp, None)
            tempDict = {}

            if des_img_inp is not None:
                tempDict[1] = des_img_inp.tolist()
            if des_img_inp is None:
                tempDict[1] = []
            allFeatures[i+1] = tempDict

        return allFeatures

    # **
    # Match features of 2 images
    # **
    def imageMatcher(self, img_orig_feat, img_tocheck):

        with open(img_orig_feat, 'rb') as handle:
            img_orig_feat = pickle.load(handle)

        # read input image and comparing image
        img_tocomp = cv2.imread(img_tocheck)

        # extract height width channels
        width1 = img_orig_feat[0][1]
        height1 = img_orig_feat[0][2]
        height2, width2, channels2 = img_tocomp.shape

        # =========== extract luminance values ===========
        lum_img_tocomp = cv2.cvtColor(img_tocomp, cv2.COLOR_BGR2LAB)
        lum = img_orig_feat[0][0]
        print("Avg. Lumination IMG_INP: ", lum)

        lum2, a, b = cv2.split(lum_img_tocomp)
        lum_vals2 = np.array(lum2)
        print("Avg. Lumination IMG_TOCOMP: ", np.mean(lum_vals2))

        #  =========== calculate coefficients ===========
        # for description see documentation
        DISTANCE_COEFF = 0.50
        COMP_COEFF = 0.1
        SPLIT_COEFF = 4

        # calculating distance relations
        if (width1 > width2):
            tmp = math.trunc(width1 / width2)
            DISTANCE_COEFF = DISTANCE_COEFF + (0.045 * tmp)
            if (tmp > 1):
                tmp = math.trunc(tmp / 2)
            COMP_COEFF = COMP_COEFF / (10 ** (tmp))

        if (width1 < width2):
            tmp = math.trunc(width2 / width1)
            DISTANCE_COEFF = DISTANCE_COEFF + (0.045 * tmp)
            if (tmp > 1):
                tmp = math.trunc(tmp / 2)
            COMP_COEFF = COMP_COEFF / (10 ** (tmp))

        # calculating luminance relations
        lumdiff = abs(lum - np.mean(lum_vals2))
        glum = 0
        if (lum > np.mean(lum_vals2)):
            glum = lum
        if (lum <= np.mean(lum_vals2)):
            glum = np.mean(lum_vals2)

        if (lumdiff / glum > 0.25 and COMP_COEFF == 0.1):
            COMP_COEFF = COMP_COEFF / 10
            if (glum / np.mean(lum_vals2) > 0.50):
                COMP_COEFF = COMP_COEFF / 10

        # =========== Segment images ===========
        width_1_new = img_orig_feat[0][1] // SPLIT_COEFF
        height_1_new = img_orig_feat[0][2] // SPLIT_COEFF
        width_2_new = width2 // SPLIT_COEFF
        height_2_new = height2 // SPLIT_COEFF
        counter_row = 0
        counter_col = 0
        multiplicator_row = 0
        multiplicator_col = -1
        hitcount = 0

        # do calculations for every segment
        for i in range(SPLIT_COEFF ** 2):
            if (i % SPLIT_COEFF == 0):
                multiplicator_row = 0
                multiplicator_col += 1

            # split both images
            prt2 = img_tocomp[height_2_new * multiplicator_row:height_2_new * (multiplicator_row + 1),
                   width_2_new * multiplicator_col:width_2_new * (multiplicator_col + 1)]
            multiplicator_row += 1;

            # ORB Algorithm (efficient alternative to SIFT)
            # Keypoint and descriptor extraction
            orb = cv2.ORB_create(50, 1.2, nlevels=8, edgeThreshold=5)
            gray_img_tocomp = cv2.cvtColor(prt2, cv2.COLOR_BGR2GRAY)
            kp_img_tocomp, des_img_tocomp = orb.detectAndCompute(gray_img_tocomp, None)
            des_img_inp = img_orig_feat[i+1][1]

            # If keypoints and descriptors are found in poth image segments they will be matched now
            if des_img_inp is not None:
                if (len(kp_img_tocomp) > 0 and len(des_img_inp) > 0 and len(des_img_tocomp) > 0):

                    # FLANN k nearest neighbor matching
                    FLANN_INDEX_KDTREE = 0
                    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                    search_params = dict(checks=50)

                    flannMatcher = cv2.FlannBasedMatcher(index_params, search_params)
                    des_img_inp = np.float32(des_img_inp)
                    des_img_tocomp = np.float32(des_img_tocomp)

                    allmatches = flannMatcher.knnMatch(des_img_inp, des_img_tocomp,2)  # it searches the 2 nearest neighbors

                    # Lowe´s matching ratio [2,p.19f]
                    acceptedMatches = []
                    for n1, n2 in allmatches:
                        if n1.distance < DISTANCE_COEFF * n2.distance:
                            acceptedMatches.append(n1)

                    print("ACCEPTED: %d ALL: " % len(acceptedMatches), len(allmatches))

                    # Ratio for accepted exact matches of image segment
                    print(len(acceptedMatches) / len(allmatches))
                    if len(acceptedMatches) / len(
                            allmatches) > COMP_COEFF:  # if greater than the expected ratio the certain segment is accepted
                        hitcount = hitcount + 1

        # if at least 50% of the image segments are accepted because of enough exact matching keypoints, the image in general is identified
        result = 'NOT IDENTIFIED'
        if hitcount >= SPLIT_COEFF + (SPLIT_COEFF / 2):
            print("===> IMAGE IDENTIFIED %d" % hitcount)
            result = 'IDENTIFIED'
        if hitcount < SPLIT_COEFF + (SPLIT_COEFF / 2):
            result = 'NOT IDENTIFIED'
            print("===> IMAGE FAILED %d" % hitcount)

        return result
