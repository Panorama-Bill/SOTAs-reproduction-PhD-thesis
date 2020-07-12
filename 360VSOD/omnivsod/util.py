import os
import torch
from spherical_distortion.util import load_torch_img, torch2numpy
from spherical_distortion.functional import create_tangent_images, tangent_images_to_equirectangular
from torch.autograd import Variable


def listTrain():
    f1 = open(os.getcwd() + '/train_img.lst', 'w')
    f2 = open(os.getcwd() + '/train_msk.lst', 'w')
    f3 = open(os.getcwd() + '/test_img.lst', 'w')
    f4 = open(os.getcwd() + '/test_msk.lst', 'w')
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
                f3.write(lineImg)
                f4.write(lineMsk)
                frm_count += 1
    print(" {} frames wrote. ".format(frm_count))
    f1.close()
    f2.close()
    f3.close()
    f4.close()

def ER2TI(ER):
    base_order = 1  # Determines the number of planes and their location on sphere
    sample_order = 10  # Determines the sample resolution

    ER = ER.cuda()
    TIs = create_tangent_images(ER, base_order, sample_order)
    TIs = TIs.permute(1, 0, 2, 3)

    return TIs

def TI2ER():
    print()


if __name__ == '__main__':
    #listTrain()
    ER2TI()