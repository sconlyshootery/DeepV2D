import sys
sys.path.append('deepv2d')

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

import argparse
import cv2
import os
import time
import glob
import random

from deepv2d.core import config
from deepv2d.deepv2d import DeepV2D
import warnings

warnings.filterwarnings('ignore')


def load_test_sequence(path, n_frames=-1):
    """ loads images and intrinsics from demo folder """
    images = []
    for imfile in sorted(glob.glob(os.path.join(path, "*.png"))):
        img = cv2.imread(imfile)
        images.append(img)

    inds = np.arange(1, len(images))
    if n_frames > 0:
        inds = np.random.choice(inds, n_frames, replace=False)

    inds = [0] + inds.tolist() # put keyframe image first
    images = [images[i] for i in inds]

    images = np.stack(images).astype(np.float32)
    intrinsics = np.loadtxt(os.path.join(path, 'intrinsics.txt'))

    return images, intrinsics


def main(args):

    if args.cfg is None:
        if 'nyu' in args.model:
            args.cfg = '/home/sconly/Documents/code/DeepV2D/cfgs/nyu.yaml'
        elif 'scannet' in args.model:
            args.cfg = '/home/sconly/Documents/code/DeepV2D/cfgs/scannet.yaml'
        elif 'kitti' in args.model:
            args.cfg = '/home/sconly/Documents/code/DeepV2D/cfgs/kitti.yaml'
        else:
            args.cfg = '/home/sconly/Documents/code/DeepV2D/cfgs/nyu.yaml'
        
    cfg = config.cfg_from_file(args.cfg)
    is_calibrated = not args.uncalibrated

    # build the DeepV2D graph
    deepv2d = DeepV2D(cfg, args.model, use_fcrn=args.fcrn, is_calibrated=is_calibrated, mode=args.mode)

    gpu_no = '0' # or '1'
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_no

    # 定义TensorFlow配置
    conf = tf.ConfigProto()

    # 配置GPU内存分配方式，按需增长，很关键
    conf.gpu_options.allow_growth = True

    # 配置可使用的显存比例
    # conf.gpu_options.per_process_gpu_memory_fraction = 0.8

    with tf.Session(config = conf) as sess:
        deepv2d.set_session(sess)

        # call deepv2d on a video sequence
        images, intrinsics = load_test_sequence(args.sequence)
        
        if is_calibrated:
            depths, poses = deepv2d(images, intrinsics, viz=True, iters=args.n_iters)
        else:
            depths, poses = deepv2d(images, viz=True, iters=args.n_iters)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', help='config file used to train the model')
    parser.add_argument('--model', default='/home/sconly/Documents/code/DeepV2D/models/kitti.ckpt', help='path to model checkpoint')
    
    parser.add_argument('--mode', default='keyframe', help='keyframe or global pose optimization')
    parser.add_argument('--fcrn', action="store_true", help='use fcrn for initialization', default=False)
    parser.add_argument('--n_iters', type=int, default=5, help='number of iterations to use')
    parser.add_argument('--uncalibrated', action="store_true", help='use fcrn for initialization', default=False)
    parser.add_argument('--sequence', help='path to sequence folder', default='/home/sconly/Documents/code/DeepV2D/data/demos/kitti_0')
    args = parser.parse_args()

    main(args)
