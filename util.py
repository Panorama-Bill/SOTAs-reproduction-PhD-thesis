import os
import torch
from spherical_distortion.util import load_torch_img, torch2numpy
from spherical_distortion.functional import create_tangent_images, tangent_images_to_equirectangular
from torch.autograd import Variable
import torch.nn.functional as F
import cv2
import numpy as np


def listTrain():
    f1 = open(os.getcwd() + '/train_img.lst', 'w')
    f2 = open(os.getcwd() + '/train_msk.lst', 'w')
    f3 = open(os.getcwd() + '/test_img.lst', 'w')
    f4 = open(os.getcwd() + '/test_msk.lst', 'w')
    f5 = open(os.getcwd() + '/test_ins_lst', 'w')
    frm_count = 0
    for cls in os.listdir(os.getcwd() + '/data/train_img/'):
        for vid in os.listdir(os.path.join(os.getcwd() + '/data/train_img/', cls)):
            vidList = os.listdir(os.path.join(os.path.join(os.getcwd() + '/data/train_img/', cls), vid))
            vidList.sort(key=lambda x: x[:-4])
            for frm in vidList:
                lineImg = os.path.join(os.path.join(os.path.join(os.getcwd() + '/data/train_img/', cls), vid), frm) + \
                          '\n'
                lineMsk = os.path.join(os.path.join(os.path.join(os.getcwd() + '/data/train_msk/', cls), vid),
                                       'frame_' + frm[-10:]) + '\n'
                f1.write(lineImg)
                f2.write(lineMsk)
                frm_count += 1
    print(" {} frames wrote. ".format(frm_count))
    for cls in os.listdir(os.getcwd() + '/data/test_img/'):
        for vid in os.listdir(os.path.join(os.getcwd() + '/data/test_img/', cls)):
            vidList = os.listdir(os.path.join(os.path.join(os.getcwd() + '/data/test_img/', cls), vid))
            vidList.sort(key=lambda x: x[:-4])
            for frm in vidList:
                lineImg = os.path.join(os.path.join(os.path.join(os.getcwd() + '/data/test_img/', cls), vid), frm) + \
                          '\n'
                lineMsk = os.path.join(os.path.join(os.path.join(os.getcwd() + '/data/test_msk/', cls), vid),
                                       'frame_' + frm[-10:]) + '\n'
                lineIns = os.path.join(os.path.join(os.path.join(os.getcwd() + '/data/test_ins/', cls), vid),
                                       'frame_' + frm[-10:]) + '\n'
                f3.write(lineImg)
                f4.write(lineMsk)
                f5.write(lineIns)
                frm_count += 1
    print(" {} frames wrote. ".format(frm_count))
    f1.close()
    f2.close()
    f3.close()
    f4.close()
    f5.close()

def ER2TI(ER, base_order, sample_order):
    #ER = ER.cuda() # not suggested for the dataload get_item process
    TIs = create_tangent_images(ER, base_order, sample_order)
    TIs = TIs.permute(1, 0, 2, 3)

    return TIs

def TI2ER(TIs, base_level, sample_level):
    ER = tangent_images_to_equirectangular(TIs, [int(2048 / 2 ** (10 - sample_level)),
                                                     int(4096 / 2 ** (10 - sample_level))],
                                           base_level, sample_level)

    return ER

def demo():
    img_pth = os.getcwd() + '/results_analysis/Img/'
    gt_pth = os.getcwd() + '/results_analysis/GT/'
    ins_pth = os.getcwd() + '/results_analysis/InsGT/'
    salEr_pth = os.getcwd() + '/results_analysis/Sal_ER_FcnResNet101/'
    salTi_pth = os.getcwd() + '/results_analysis/Sal_TI_S7B0_FcnResNet101/'
    salBasnet = os.getcwd() + '/results_analysis/Sal_basnet/'
    salCpdr = os.getcwd() + '/results_analysis/Sal_cpd-r/'
    salEgnet = os.getcwd() + '/results_analysis/Sal_egnet/'
    salF3net = os.getcwd() + '/results_analysis/Sal_f3net/'
    salPoolnet = os.getcwd() + '/results_analysis/Sal_poolnet/'
    salScribbleSOD = os.getcwd() + '/results_analysis/Sal_scribbleSOD/'
    salScrn = os.getcwd() + '/results_analysis/Sal_scrn/'
    salRcrnet = os.getcwd() + '/results_analysis/Sal_rcrnet/'


    demo = cv2.VideoWriter(os.getcwd() + '/' + 'demo.avi', 0, 100, (1536, 1280))
    img_list = os.listdir(img_pth)
    img_list.sort(key=lambda x: x[:-4])

    count = 1
    for item in img_list:
        img = cv2.imread(img_pth + item)
        gt = cv2.imread(gt_pth + item)
        ins = cv2.imread(ins_pth + item)
        salEr = cv2.imread(salEr_pth + item)
        salTi = cv2.imread(salTi_pth + item)
        salBas = cv2.imread(salBasnet + item)
        salCpd = cv2.imread(salCpdr + item)
        salEgn = cv2.imread(salEgnet + item)
        salF3n = cv2.imread(salF3net + item)
        salPoo = cv2.imread(salPoolnet + item[:-4] + '_sal_fuse.png')
        salSSOD = cv2.imread(salScribbleSOD + item)
        salScr = cv2.imread(salScrn + item)
        salRcr = cv2.imread(salRcrnet + item)


        frm = np.zeros((1280, 1536, 3))
        frm[:256, :512, :] = img
        frm[:256, 512:1024, :] = gt
        frm[:256, 1024:, :] = ins

        frm[256:512, :512, :] = salEr
        frm[256:512, 512:1024, :] = salTi
        frm[256:512, 1024:, :] = salBas

        frm[512:768, :512, :] = salCpd
        frm[512:768, 512:1024, :] = salEgn
        frm[512:768, 1024:, :] = salF3n

        frm[768:1024, :512, :] = salPoo
        frm[768:1024, 512:1024, :] = salSSOD
        frm[768:1024, 1024:, :] = salScr

        frm[1024:, :512, :] = salRcr

        demo.write(np.uint8(frm))
        print("{} writen".format(count))
        count += 1

    demo.release()

def demo_facile():
    img_pth = os.getcwd() + '/result_analysis/GTs/Img/'
    sal_pth = os.getcwd() + '/result_analysis/Sal_test_raft_kitti/'

    demo = cv2.VideoWriter(os.getcwd() + '/' + 'demo.avi', 0, 100, (1024, 256))
    img_list = os.listdir(img_pth)
    img_list.sort(key=lambda x: x[:-4])

    count = 1
    for item in img_list:
        img = cv2.imread(img_pth + item)
        sal = cv2.imread(sal_pth + item)

        frm = np.zeros((256, 1024, 3))
        frm[:256, :512, :] = img
        frm[:256, 512:1024, :] = sal

        demo.write(np.uint8(frm))
        print("{} writen".format(count))
        count += 1

    demo.release()

def listTest():
    img_pth = os.getcwd() + '/results_analysis/Img/'
    img_list = os.listdir(img_pth)
    img_list.sort(key=lambda x: x[:-4])
    f = open(os.getcwd() + '/test.lst', 'w')

    for item in img_list:
        f.write(item + '\n')
    f.close()

def normPRED(d):
    ma = torch.max(d)
    mi = torch.min(d)
    dn = (d-mi)/(ma-mi)

    return dn


if __name__ == '__main__':
    print()
    #listTrain()
    #ER2TI()
    demo_facile()
    #listTest()
