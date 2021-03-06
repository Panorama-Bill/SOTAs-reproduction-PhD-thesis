import os
from PIL import Image
import torch
from torch.utils import data
from torchvision import transforms
import matplotlib.pyplot as plt
#from util import ER2TI
import torch.nn.functional as F
import cv2
import numpy as np
from py360convert import e2c
from equiPers.equir2pers import equir2pers


class ImageDataTrain(data.Dataset):
    def __init__(self, data_type, base_level, sample_level, data_norm, data_pair, data_flow, data_sound):
        self.img_source = os.getcwd() + '/data/train_img.lst'
        self.msk_source = os.getcwd() + '/data/train_msk.lst'
        #self.img_source = os.getcwd() + '/data/train_img_FS.lst'
        #self.msk_source = os.getcwd() + '/data/train_msk_FS.lst'
        self.data_type = data_type
        self.base_level = base_level
        self.sample_level = sample_level
        self.data_norm = data_norm
        self.data_pair = data_pair
        self.data_flow = data_flow
        self.data_sound = data_sound

        with open(self.img_source, 'r') as f:
            self.img_list = [x.strip() for x in f.readlines()]
        with open(self.msk_source, 'r') as f:
            self.msk_list = [x.strip() for x in f.readlines()]

        self.img_num = len(self.img_list)

    def __getitem__(self, item):
        if self.data_type == 'G':
            ER_img = load_ERImg(self.img_list[item % self.img_num], self.data_norm)
            ER_msk = load_ERMsk(self.msk_list[item % self.img_num])

            sample = {'ER_img': ER_img, 'ER_msk': ER_msk}

            if self.data_pair == True:
                if item <= (self.img_num - 10):
                    ER_img_next = load_ERImg(self.img_list[(item+10) % self.img_num], self.data_norm)
                    ER_msk_next = load_ERMsk(self.msk_list[(item+10) % self.img_num])
                else:
                    ER_img_next = ER_img
                    ER_msk_next = ER_msk

                sample = {'ER_img': ER_img, 'ER_msk': ER_msk, 'ER_img_next': ER_img_next, 'ER_msk_next': ER_msk_next}

            elif self.data_flow == True:
                frm_name = self.img_list[item % self.img_num][53:]
                name_list = frm_name.split('/')
                frm_name = name_list[0] + '-' + name_list[1] + '-' + name_list[2]
                flow_pth = os.path.join(os.getcwd(), 'data', 'flow_train_raft_sintel', frm_name)
                ER_flow = load_ERImg(flow_pth, self.data_norm)

                sample = {'ER_img': ER_img, 'ER_msk': ER_msk, 'ER_flow': ER_flow}

        elif self.data_type == 'L':
            TI_imgs = load_TIImg(self.img_list[item % self.img_num], self.base_level, self.sample_level)
            #ER_msk = load_ERMsk(self.msk_list[item % self.img_num])
            TI_msks = load_TIMsk(self.msk_list[item % self.img_num], self.base_level, self.sample_level)

            sample = {'TI_imgs': TI_imgs, 'TI_msks': TI_msks}

        elif self.data_type == 'EC':
            ER_img = load_ERImg(self.img_list[item % self.img_num], self.data_norm)
            CM_imgs = load_CMImg(self.img_list[item % self.img_num], self.data_norm)
            ER_msk = load_ERMsk(self.msk_list[item % self.img_num])
            CM_msks = load_CMMsk(self.msk_list[item % self.img_num])

            if self.data_sound == True:
                # match the sound maps
                frm_name = self.img_list[item % self.img_num][53:]
                category_name = frm_name.split('/')[2][:-11]
                sound_list = os.listdir(os.getcwd() + '/data/Sound_enhance/')
                if category_name in sound_list:
                    Sound_map = load_SoundMap(os.path.join(os.getcwd() + '/data/Sound_enhance/', category_name,
                                                           category_name + '.png'))
                else:
                    Sound_map = load_SoundMap(os.getcwd() + '/data/Sound_enhance/zero_map.png')
                    Sound_map = 1 - Sound_map

                sample = {'ER_img': ER_img, 'ER_msk': ER_msk, 'CM_imgs': CM_imgs, 'CM_msks': CM_msks,
                          'Sound_map': Sound_map}

            else:
                sample = {'ER_img': ER_img, 'ER_msk': ER_msk, 'CM_imgs': CM_imgs, 'CM_msks': CM_msks}

        return sample

    def __len__(self):
        return self.img_num

class ImageDataTest(data.Dataset):
    def __init__(self, data_type, base_level, sample_level, need_ref, data_norm, data_pair, data_flow, data_sound):
        self.img_source = os.getcwd() + '/data/test_img.lst'
        #self.img_source = os.getcwd() + '/data/test_img_FS.lst'
        self.data_type = data_type
        self.base_level = base_level
        self.sample_level = sample_level
        self.need_ref = need_ref
        self.data_norm = data_norm
        self.data_pair = data_pair
        self.data_flow = data_flow
        self.data_sound = data_sound
        #self.ins_source = os.getcwd() + '/data/test_ins.lst'
      #  self.gt_source = os.getcwd() + '/data/train_msk.lst'

        with open(self.img_source, 'r') as f:
            self.img_list = [x.strip() for x in f.readlines()]
        #with open(self.gt_source, 'r') as f:
        #    self.gt_list = [x.strip() for x in f.readlines()]

        self.img_num = len(self.img_list)

    def __getitem__(self, item):
        frm_name = self.img_list[item % self.img_num][52:]
        name_list = frm_name.split('/')
        frm_name = name_list[0] + '-' + name_list[1] + '-' + name_list[2]

        if self.data_type == 'G':
            ER_img = load_ERImg(self.img_list[item % self.img_num], self.data_norm)

            if self.need_ref == False:
                # ER_ins = load_ERMsk(self.ins_list[item % self.img_num])
                sample = {'ER_img': ER_img, 'frm_name': frm_name}
                #prep_score(self.gt_list[item % self.img_num], frm_name)
                # prep_ins(self.ins_list[item % self.img_num], frm_name)
            else:
                refFrm_pth = []
                Ref_img = []
                [refFrm_pth.append(idx) for idx in self.img_list if idx[:-10] == self.img_list[item][:-10]]
                Ref_img.append(load_ERImg(refFrm_pth[0], self.data_norm)) # only choose the first frame as reference
               # [Ref_img.append(load_ERImg(pth, self.data_norm)) for pth in refFrm_pth]

                sample = {'ER_img': ER_img, 'frm_name': frm_name, 'Ref_img': Ref_img}

                #prep_demo(self.img_list[item % self.img_num], self.gt_list[item % self.img_num], frm_name)

            if self.data_pair == True:
                if item != self.img_num - 1:
                    ER_img_next = load_ERImg(self.img_list[(item+1) % self.img_num], self.data_norm)
                else:
                    ER_img_next = ER_img

                sample = {'ER_img': ER_img, 'frm_name': frm_name, 'ER_img_next': ER_img_next}

            if self.data_flow == True:
                flow_pth = os.path.join(os.getcwd(), 'data', 'Sal_test_raft_sintel', frm_name)
                ER_flow = load_ERImg(flow_pth, self.data_norm)
                sample = {'ER_img': ER_img, 'frm_name': frm_name, 'ER_flow': ER_flow}

        elif self.data_type == 'L':
            TI_imgs = load_TIImg(self.img_list[item % self.img_num], self.base_level, self.sample_level)
            sample = {'TI_imgs': TI_imgs, 'frm_name': frm_name}

        elif self.data_type == 'EC':
            ER_img = load_ERImg(self.img_list[item % self.img_num], self.data_norm)
           # sample = {'ER_img': ER_img, 'frm_name': frm_name}
            CM_imgs = load_CMImg(self.img_list[item % self.img_num], self.data_norm)

            if self.data_sound == True:
                # match the sound maps
                category_name_ = self.img_list[item % self.img_num][52:]
                category_name = category_name_.split('/')[2][:-11]
                sound_list = os.listdir(os.getcwd() + '/data/Sound_enhance/')
                if category_name in sound_list:
                    Sound_map = load_SoundMap(os.path.join(os.getcwd() + '/data/Sound_enhance/', category_name,
                                                           category_name + '.png'))
                else:
                    Sound_map = load_SoundMap(os.getcwd() + '/data/Sound_enhance/zero_map.png')
                    Sound_map = 1 - Sound_map

                sample = {'ER_img': ER_img, 'frm_name': frm_name, 'CM_imgs': CM_imgs, 'Sound_map': Sound_map}

            else:
                sample = {'ER_img': ER_img, 'frm_name': frm_name, 'CM_imgs': CM_imgs}

        return sample

    def __len__(self):
        return self.img_num

# get the dataloader (Note: without data augmentation, except saliency with random flip)
def get_loader(batch_size, mode='train', num_thread=1, data_type='G', base_level = 1, sample_level=10, ref=False,
               norm='cv2', pair=False, flow=False, sound=False):
    shuffle = False
    if mode == 'train':
        shuffle = True
        dataset = ImageDataTrain(data_type=data_type, base_level=base_level, sample_level=sample_level,
                                 data_norm=norm, data_pair=pair, data_flow=flow, data_sound=sound)
    else:
        dataset = ImageDataTest(data_type=data_type, base_level=base_level, sample_level=sample_level,
                                need_ref=ref, data_norm=norm, data_pair=pair, data_flow=flow, data_sound=sound)

    data_loader = data.DataLoader(dataset=dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_thread)

    return data_loader, dataset

def load_SoundMap(pth):
    if not os.path.exists(pth):
        print('File Not Exists')
    map = Image.open(pth)
    map = map.convert(mode='L')
    preprocess = transforms.Compose([
        transforms.ToTensor(),
    ])
    map_tensor = preprocess(map)

    return map_tensor

def load_ERImg(pth, norm):
    if not os.path.exists(pth):
        print('File Not Exists')
    if norm == 'cv2':
        im = cv2.imread(pth)
        im = cv2.resize(im, (512, 256))
        in_ = np.array(im, dtype=np.float32)
        in_ -= np.array((104.00699, 116.66877, 122.67892))
        in_ = in_.transpose((2, 0, 1))
        in_ = torch.Tensor(in_)
    elif norm == 'PIL':
        im = Image.open(pth)
        preprocess = transforms.Compose([
            transforms.Resize([256, 512]),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        in_ = preprocess(im)

    return in_

def load_CMImg_1(pth, norm):
    if not os.path.exists(pth):
        print('File Not Exists')
    if norm == 'PIL':
        im = cv2.imread(pth)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        cubes = e2c(im)  # F R B L U D
        in_F = cubes[0]
        in_F = Image.fromarray(in_F)
        in_R = cubes[1]
        in_R = Image.fromarray(in_R)
        in_R = in_R.transpose(Image.FLIP_LEFT_RIGHT)
        in_B = cubes[2]
        in_B = Image.fromarray(in_B)
        in_B = in_B.transpose(Image.FLIP_LEFT_RIGHT)
        in_L = cubes[3]
        in_L = Image.fromarray(in_L)
        in_U = cubes[4]
        in_U = Image.fromarray(in_U)
        in_U = in_U.transpose(Image.FLIP_TOP_BOTTOM)
        in_D = cubes[5]
        in_D = Image.fromarray(in_D)
        preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        in_F = preprocess(in_F)
        in_R = preprocess(in_R)
        in_B = preprocess(in_B)
        in_L = preprocess(in_L)
        in_U = preprocess(in_U)
        in_D = preprocess(in_D)

        return in_F, in_R, in_B, in_L, in_U, in_D

def load_CMImg(pth, norm):
    if not os.path.exists(pth):
        print('File Not Exists')
    if norm == 'PIL':
        im = cv2.imread(pth)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        in_F = equir2pers(im, 112.5, 0, 0, 384, 384)  # F
        in_F = Image.fromarray(in_F)
        in_R = equir2pers(im, 112.5, 90, 0, 384, 384)  # R
        in_R = Image.fromarray(in_R)
        in_B = equir2pers(im, 112.5, 180, 0, 384, 384)  # B
        in_B = Image.fromarray(in_B)
        in_L = equir2pers(im, 112.5, -90, 0, 384, 384)  # L
        in_L = Image.fromarray(in_L)
        in_U = equir2pers(im, 112.5, 0, 90, 384, 384)  # U
        in_U = Image.fromarray(in_U)
        in_D = equir2pers(im, 112.5, 0, -90, 384, 384)  # D
        in_D = Image.fromarray(in_D)
        preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        in_F = preprocess(in_F)
        in_R = preprocess(in_R)
        in_B = preprocess(in_B)
        in_L = preprocess(in_L)
        in_U = preprocess(in_U)
        in_D = preprocess(in_D)

        return in_F, in_R, in_B, in_L, in_U, in_D

def load_ERMsk(pth):
    if not os.path.exists(pth):
        print('File Not Exists')
    msk = Image.open(pth)
    preprocess = transforms.Compose([
        transforms.Resize([256, 512]),
        transforms.ToTensor(),
    ])
    msk_tensor = preprocess(msk)

    return msk_tensor

def load_CMMsk_1(pth):
    if not os.path.exists(pth):
        print('File Not Exists')
    msk = cv2.imread(pth)
    msk = cv2.cvtColor(msk, cv2.COLOR_BGR2RGB)
    cubes = e2c(msk)
    in_F = cubes[0]
    in_F = Image.fromarray(in_F)
    in_F = in_F.convert(mode='L')
    in_R = cubes[1]
    in_R = Image.fromarray(in_R)
    in_R = in_R.convert(mode='L')
    in_R = in_R.transpose(Image.FLIP_LEFT_RIGHT)
    in_B = cubes[2]
    in_B = Image.fromarray(in_B)
    in_B = in_B.convert(mode='L')
    in_B = in_B.transpose(Image.FLIP_LEFT_RIGHT)
    in_L = cubes[3]
    in_L = Image.fromarray(in_L)
    in_L = in_L.convert(mode='L')
    in_U = cubes[4]
    in_U = Image.fromarray(in_U)
    in_U = in_U.convert(mode='L')
    in_U = in_U.transpose(Image.FLIP_TOP_BOTTOM)
    in_D = cubes[5]
    in_D = Image.fromarray(in_D)
    in_D = in_D.convert(mode='L')

    preprocess = transforms.Compose([
        transforms.ToTensor(),
    ])
    in_F = preprocess(in_F)
    in_R = preprocess(in_R)
    in_B = preprocess(in_B)
    in_L = preprocess(in_L)
    in_U = preprocess(in_U)
    in_D = preprocess(in_D)

    return in_F, in_R, in_B, in_L, in_U, in_D

def load_CMMsk(pth):
    if not os.path.exists(pth):
        print('File Not Exists')
    im = cv2.imread(pth)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    in_F = equir2pers(im, 112.5, 0, 0, 384, 384)  # F
    in_F = Image.fromarray(in_F)
    in_F = in_F.convert(mode='L')
    in_R = equir2pers(im, 112.5, 90, 0, 384, 384)  # R
    in_R = Image.fromarray(in_R)
    in_R = in_R.convert(mode='L')
    in_B = equir2pers(im, 112.5, 180, 0, 384, 384)  # B
    in_B = Image.fromarray(in_B)
    in_B = in_B.convert(mode='L')
    in_L = equir2pers(im, 112.5, -90, 0, 384, 384)  # L
    in_L = Image.fromarray(in_L)
    in_L = in_L.convert(mode='L')
    in_U = equir2pers(im, 112.5, 0, 90, 384, 384)  # U
    in_U = Image.fromarray(in_U)
    in_U = in_U.convert(mode='L')
    in_D = equir2pers(im, 112.5, 0, -90, 384, 384)  # D
    in_D = Image.fromarray(in_D)
    in_D = in_D.convert(mode='L')
    preprocess = transforms.Compose([
        transforms.ToTensor(),
    ])
    in_F = preprocess(in_F)
    in_R = preprocess(in_R)
    in_B = preprocess(in_B)
    in_L = preprocess(in_L)
    in_U = preprocess(in_U)
    in_D = preprocess(in_D)

    return in_F, in_R, in_B, in_L, in_U, in_D

def prep_demo(img_pth, gt_pth, name):
    img = Image.open(img_pth)
    img = img.resize((512, 256))
    gt = Image.open(gt_pth)
    gt = gt.resize((512, 256))
    img.save('/home/yzhang1/PythonProjects/omnivsod/results/Img/' + name)
    gt.save('/home/yzhang1/PythonProjects/omnivsod/results/GT/' + name)

def prep_score(gt_pth, name):
    gt = Image.open(gt_pth)
    gt.save('/home/yzhang1/PythonProjects/omnivsod/results/GT_ori/' + name)

def prep_ins(ins_pth, name):
    ins = Image.open(ins_pth)
    ins = ins.resize((512, 256))
    ins.save('/home/yzhang1/PythonProjects/omnivsod/results/InsGT/' + name)

def load_TIImg(pth, base_level, sample_level):
    if not os.path.exists(pth):
        print('File Not Exists')
    ER_img = Image.open(pth)

    preprocess = transforms.Compose([
        transforms.Resize([int(2048 / 2 ** (10 - sample_level)), int(4096 / 2 ** (10 - sample_level))]),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    ER_img_tensor = preprocess(ER_img)
    TI_imgs = ER2TI(ER_img_tensor, base_level, sample_level)

    return TI_imgs

def load_TIMsk(pth, base_level, sample_level):
    if not os.path.exists(pth):
        print('File Not Exists')
    ER_msk = Image.open(pth)
    preprocess = transforms.Compose([
        transforms.Resize([int(2048 / 2 ** (10 - sample_level)), int(4096 / 2 ** (10 - sample_level))]),
        transforms.ToTensor(),
    ])
    ER_msk_tensor = preprocess(ER_msk)
    TI_msks = ER2TI(ER_msk_tensor, base_level, sample_level)

    return TI_msks


#if self.data_sound == True:
    # match the sound maps
#    frm_name = self.img_list[item % self.img_num][53:]
 #   category_name = frm_name.split('/')[2][:-11]
  #  sound_list = os.listdir(os.getcwd() + '/data/sound_map/')
   # if category_name in sound_list:
    #    Sound_map = load_SoundMap(os.path.join(os.getcwd() + '/data/sound_map/', category_name,
     #                                          'frame_' + frm_name.split('/')[2][-10:]))
    #else:
     #   Sound_map = load_SoundMap(os.getcwd() + '/data/sound_map/Zero/frame_000000.png')

    #sample = {'ER_img': ER_img, 'ER_msk': ER_msk, 'CM_imgs': CM_imgs, 'CM_msks': CM_msks,
     #         'Sound_map': Sound_map}