import torch
from collections import OrderedDict
from torch.nn import utils, functional as F
from torch.optim import Adam, SGD
from torch.autograd import Variable
from torch.backends import cudnn
from model import build_model
import scipy.misc as sm
import numpy as np
import os
import torchvision.utils as vutils
import cv2
import torch.nn.functional as F
import math
import time
import sys
import PIL.Image
import scipy.io
import os
import logging
import matplotlib.pyplot as plt


class Solver(object):
    def __init__(self, train_loader, test_loader, config):
        self.train_loader = train_loader
        self.test_loader = test_loader
        self.config = config
        if config.visdom:
            self.visual = Viz_visdom("trueUnify", 1)
        self.build_model()
        if self.config.pre_trained: self.net_bone.load_state_dict(torch.load(self.config.pre_trained))
        if config.mode == 'train':

            print()
        else:
            print('Loading pre-trained model from %s...' % self.config.model)
            self.net_bone.load_state_dict(torch.load(self.config.model))
            self.net_bone.eval()

    def print_network(self, model, name):
        num_params = 0
        for p in model.parameters():
            num_params += p.numel()
        print(name)
        print(model)
        print("The number of parameters: {}".format(num_params))

    def get_params(self, base_lr):
        ml = []
        for name, module in self.net_bone.named_children():
            print(name)
            if name == 'loss_weight':
                ml.append({'params': module.parameters(), 'lr': p['lr_branch']})          
            else:
                ml.append({'params': module.parameters()})
        return ml

    # build the network
    def build_model(self):
        print('model under built...')

    # update the learning rate
    def update_lr(self, rate):
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = param_group['lr'] * rate


    def test(self, test_mode=0):
        EPSILON = 1e-8
        img_num = len(self.test_loader)
        time_t = 0.0
        name_t = 'EGNet_ResNet50/'


        for i, data_batch in enumerate(self.test_loader):

          #  print(self.config.test_fold)
            images_, name, im_size = data_batch['image'], data_batch['name'][0], np.asarray(data_batch['size'])
            
            with torch.no_grad():
                
                images = Variable(images_)
                if self.config.cuda:
                    images = images.cuda()
               # print(images.size())
                time_start = time.time()
                up_edge, up_sal, up_sal_f = self.net_bone(images)
                torch.cuda.synchronize()
                time_end = time.time()
                #print(time_end - time_start)
                time_t = time_t + time_end - time_start                              
                pred = np.squeeze(torch.sigmoid(up_sal_f[-1]).cpu().data.numpy())             
                multi_fuse = 255 * pred
                

                
                cv2.imwrite(os.path.join(self.config.test_fold, name[:-4] + '.png'), multi_fuse)
          
        print("--- %s seconds ---" % (time_t))
        print('Test Done!')

   
    # training phase
    def train(self):
        iter_num = len(self.train_loader.dataset) // self.config.batch_size
        aveGrad = 0

        for epoch in range(self.config.epoch):                          
            r_edge_loss, r_sal_loss, r_sum_loss= 0,0,0
        #    self.net_bone.zero_grad()
            for i, data_batch in enumerate(self.train_loader):
                ER_img, ER_msk= data_batch['ER_img'], data_batch['ER_msk']
                if ER_img.size()[2:] != ER_msk.size()[2:]:
                    print("Skip this batch")
                    continue
                ER_img, ER_msk = Variable(ER_img), Variable(ER_msk)
                if self.config.cuda: 
                    ER_img, ER_msk = ER_img.cuda(), ER_msk.cuda()

                # sal part
                sal_loss1= []
                sal_loss2 = []
                for ix in up_sal:
                    sal_loss1.append(F.binary_cross_entropy_with_logits(ix, sal_label, reduction='sum'))

                for ix in up_sal_f:
                    sal_loss2.append(F.binary_cross_entropy_with_logits(ix, sal_label, reduction='sum'))
                sal_loss = (sum(sal_loss1) + sum(sal_loss2)) / (nAveGrad * self.config.batch_size)
              
                r_sal_loss += sal_loss.data
                loss = sal_loss + edge_loss
                r_sum_loss += loss.data
                loss.backward()
                aveGrad += 1

                if aveGrad % nAveGrad == 0:
       
                    self.optimizer_bone.step()
                    self.optimizer_bone.zero_grad()           
                    aveGrad = 0


                if i % showEvery == 0:

                    print('epoch: [%2d/%2d], iter: [%5d/%5d]  ||  Edge : %10.4f  ||  Sal : %10.4f  ||  Sum : %10.4f' % (
                        epoch, self.config.epoch, i, iter_num,  r_edge_loss*(nAveGrad * self.config.batch_size)/showEvery,
                                                                r_sal_loss*(nAveGrad * self.config.batch_size)/showEvery,
                                                                r_sum_loss*(nAveGrad * self.config.batch_size)/showEvery))

                    print('Learning rate: ' + str(self.lr_bone))
                    r_edge_loss, r_sal_loss, r_sum_loss= 0,0,0

              #  if i % 200 == 0:

               #     vutils.save_image(torch.sigmoid(up_sal_f[-1].data), tmp_path+'/iter%d-sal-0.jpg' % i, normalize=True, padding = 0)

                #    vutils.save_image(sal_image.data, tmp_path+'/iter%d-sal-data.jpg' % i, padding = 0)
                 #   vutils.save_image(sal_label.data, tmp_path+'/iter%d-sal-target.jpg' % i, padding = 0)
            
            if (epoch + 1) % self.config.epoch_save == 0:
                torch.save(self.net_bone.state_dict(), '%s/models/epoch_%d_bone.pth' % (self.config.save_fold, epoch + 1))
                
            if epoch in lr_decay_epoch:
                self.lr_bone = self.lr_bone * 0.1  
                self.optimizer_bone = Adam(filter(lambda p: p.requires_grad, self.net_bone.parameters()), lr=self.lr_bone, weight_decay=p['wd'])


        torch.save(self.net_bone.state_dict(), '%s/models/final_bone.pth' % self.config.save_fold)
        
def bce2d_new(input, target, reduction=None):
    assert(input.size() == target.size())
    pos = torch.eq(target, 1).float()
    neg = torch.eq(target, 0).float()
    # ing = ((torch.gt(target, 0) & torch.lt(target, 1))).float()

    num_pos = torch.sum(pos)
    num_neg = torch.sum(neg)
    num_total = num_pos + num_neg

    alpha = num_neg  / num_total
    beta = 1.1 * num_pos  / num_total
    # target pixel = 1 -> weight beta
    # target pixel = 0 -> weight 1-beta
    weights = alpha * pos + beta * neg

    return F.binary_cross_entropy_with_logits(input, target, weights, reduction=reduction)

