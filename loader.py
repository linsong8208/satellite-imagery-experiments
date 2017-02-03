from queue import Queue, Full
import random
import threading
import time
import numpy as np
import tifffile as tiff
import scipy.ndimage.interpolation


class Loader():

  def __init__(self, filenames, capacity, num_threads=1, randomize=True, augment=True):
    self.filenames = filenames
    self.data_queue = Queue(capacity)
    self.randomize = randomize
    self.threads = []
    self.augment = augment
    for i in range(num_threads):
      worker = threading.Thread(target=self.worker)
      worker.daemon = True
      self.threads.append(worker)
    self.done = False


  def start(self):
    for worker in self.threads:
      worker.start()
  

  def stop(self):
    self.done = True
    for worker in self.threads:
      worker.join()


  def get_batch(self, size):
    batch = []
    for i in range(size):
      elt = self.data_queue.get()
      batch.append(elt)
    return batch


  def worker(self):
    range_min = 0
    range_max = len(self.filenames)
    t = threading.currentThread()
    idx = 0

    while True:
      if self.done: return

      if not self.data_queue.full():
        if self.randomize:
          idx = random.randint(range_min, range_max - 1)
        else:
          idx += 1
          idx = idx % range_max
        filename = self.filenames[idx]
        try:
          input_image = tiff.imread('input_images/' + filename) 
          label_image = tiff.imread('label_images/' + filename[:-1]) 
          label_image = label_image[:, :, :1] / 255

          if self.augment:
            angle = random.randint(0, 360)
            input_image = scipy.ndimage.rotate(input_image, angle, reshape=False)
            label_image = scipy.ndimage.rotate(label_image, angle, reshape=False)

          input_image = (input_image - np.mean(input_image)) / np.std(input_image)

          self.data_queue.put_nowait((filename, input_image, label_image))
        except Full:
          pass
        except Exception as e:
          pass
          print(e)
      else:
        time.sleep(1)