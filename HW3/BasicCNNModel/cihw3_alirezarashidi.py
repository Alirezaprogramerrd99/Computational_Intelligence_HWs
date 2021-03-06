# -*- coding: utf-8 -*-
"""CIHW3_AlirezaRashidi.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tt2yKKRlkwy45yIYfCsk86gXcuKxlTAH

# Alireza Rashidi CI HW_3

## Data Preprations:
"""

from google.colab import drive
drive.mount('/content/drive')

!cp /content/drive/MyDrive/Datasets/train.zip /content/sample_data

!mkdir /content/CIHW3_Datasets
!unzip /content/sample_data/train.zip -d /content/CIHW3_Datasets

import pandas as pd
import torch
import matplotlib.pyplot as plt
import datetime
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import datasets
import torch.nn as nn
from torch import optim
from torch.nn.functional import one_hot
from torchvision.transforms import ToTensor
from tqdm import tqdm
from matplotlib import pyplot as plt

emotions = {
    0: 'Angry', 
    1: 'Disgust', 
    2: 'Fear', 
    3: 'Happy', 
    4: 'Sad', 
    5: 'Surprise', 
    6: 'Neutral'
}

df = pd.read_csv('/content/CIHW3_Datasets/train.csv')
df

# torch.cuda.is_available()
df.info()

df.groupby('emotion').count()     # printing class frequencies.

"""## Custom Dataset"""

images = []
pixels = df['pixels']

# --------------------- pure tensor -------------------------------
for row in tqdm(range(len(pixels))):
    images.append([ int(x) for x in pixels[row].split(" ") ] )

# this custom dataset used in order to batch data(with specific size) and preprocess each sample in run time.
class EmotionDetection_Dataset(torch.utils.data.Dataset):

    def __init__(self, X, y, transform=None, sample_size=(48, 48), num_classes=7, target_transform=True):
        self.X = torch.tensor(X)
        self.y = one_hot( torch.tensor(y), num_classes=num_classes) if target_transform else torch.tensor(y)  # one hot encoding for better classification accuracy
        self.transform = transform
        self.sample_size = sample_size

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        image = self.X[idx]
        image = image.reshape(1, self.sample_size[0], self.sample_size[1]) 
        label = self.y[idx]

        if self.transform:   # normalize each sample dynamicly
            image = image / 255.

        return image, label

emotion_dataset = EmotionDetection_Dataset(images, df['emotion'], transform=True, target_transform=True)
print(len(emotion_dataset))

"""## Data Visualizations:"""

sample_idx = 15;
# plt.imshow(torch.squeeze( torch.transpose(train_X_tensor[sample_idx], 0, 2), 2 ) )
plt.imshow(torch.squeeze(emotion_dataset[sample_idx][0]), cmap="gray")
print('Label: ', emotions[emotion_dataset[sample_idx][1].argmax().item()])

figure = plt.figure(figsize=(10, 8))
cols, rows = 5, 5

for i in range(1, cols * rows + 1):
    sample_idx = torch.randint(len(emotion_dataset), size=(1,)).item()
    img, label = emotion_dataset[sample_idx][0], emotions[emotion_dataset[sample_idx][1].argmax().item()]
    figure.add_subplot(rows, cols, i)
    plt.title('label: ({})'.format(label))
    plt.axis("off")
    plt.imshow(img.reshape(48, 48), cmap="gray")
plt.show()

"""## Train_validation_split:"""

random_seed = 42
torch.manual_seed(random_seed);

train_set_size = int(len(emotion_dataset) * 0.9)
valid_set_size = len(emotion_dataset) - train_set_size
train_set, valid_set = random_split(emotion_dataset, [train_set_size, valid_set_size])

print('train set len: ', len(train_set))
print('validation set len: ', len(valid_set))

"""## Using Pytorch Dataloader for batching data:"""

# batching data + creating dataloader object for training CNN in pytorch framework. 
batch_size = 64
train_dataloader = DataLoader(train_set, batch_size, shuffle=True) # we can itrate this object using iter and next in python.
val_dataloader = DataLoader(valid_set, batch_size)

print('batch images: ', iter(train_dataloader).next()[0].size())
print('batch labels: ', iter(train_dataloader).next()[1].size())

from torchvision.utils import make_grid
def show_batch(dl):
    for images, labels in dl:
        fig, ax = plt.subplots(figsize=(12, 12))
        ax.set_xticks([]); ax.set_yticks([])
        ax.imshow(make_grid(images, nrow=16).permute(1, 2, 0))
        break

print('one random batch from train_loader set (batch size = {} ): '.format(batch_size) )
show_batch(train_dataloader)

def get_default_device():
    """Pick GPU if available, else CPU"""
    if torch.cuda.is_available():
        return torch.device('cuda')
    else:
        return torch.device('cpu')

device = get_default_device()   # torch.device
print(device)

"""## Test"""

diter = iter(train_dataloader)
images, labels = diter.next()

conv1 = nn.Conv2d(in_channels=1, out_channels=64, kernel_size=3, stride=1, padding=1)
conv2 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1)
pool = nn.MaxPool2d(kernel_size=2, stride=2)
x = conv1(images)
x = pool(x)
x = conv2(x)
x = pool(x)
x = pool(x)
x = pool(x)

print(x.shape)
print(images.shape)

x = x.view(x.size(0), -1)

l1 = nn.Linear(1152, 320)
l2 = nn.Linear(320, 64)
x = l1(x)
x = l2(x)
print(x.size())

"""## CNN Model:"""

class CNN(nn.Module):   
    def __init__(self, num_classes=7):
        super(CNN, self).__init__()

        self.cnn_layers = nn.Sequential(  # image shapes(1, 48, 48)
            # vgg-16 conv layer 1------(conv1)-----------
            nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=16, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # image size will be 

            # vgg-16 conv layer 2------(conv2)-----------
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # vgg-16 conv layer 3------(conv3)-----------
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # vgg-16 conv layer 4------(conv4)-----------
            # nn.Conv2d(in_channels=256, out_channels=512, kernel_size=3, stride=1, padding=1),
            # nn.ReLU(),
            # nn.Conv2d(in_channels=512, out_channels=512, kernel_size=3, stride=1, padding=1),
            # nn.ReLU(),
            # nn.Conv2d(in_channels=512, out_channels=512, kernel_size=3, stride=1, padding=1),
            # nn.ReLU(),
            # nn.MaxPool2d(kernel_size=2, stride=2)

        )
        self.history = {'loss':[], 'val-loss':[]}

        self.linear_layers = nn.Sequential(

            nn.Linear(64 * 6 * 6, 1024),    # input features is (depth * h * w) , output feature is 128 
            nn.ReLU(),
            # nn.Dropout(p=0.30),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(p=0.30),
            nn.Linear(512, num_classes)
            )

    # Defining the forward pass (it's also prediction function)    
    def forward(self, x):
        x = self.cnn_layers(x)
        # flatten the output of conv layers to (batch_size, 512 * 3 * 3)
        x = x.view(x.size(0), -1)       
        output = self.linear_layers(x)
        return output

    def modelSummery(self):
        print(self)

cnn_model = CNN(num_classes=7).to(device)
print('CNN summery:\n')
cnn_model.modelSummery()

"""### printing models parammeters:"""

for par in cnn_model.parameters():
    print(par)

loss_func = nn.CrossEntropyLoss() 
opt = optim.Adam(cnn_model.parameters(), lr = 0.001)   
# opt2 = optim.SGD(cnn_model.parameters(), lr=0.01, momentum=0.9)
print(loss_func)
print(opt)

def train(n_epoch, opt, model, loss_func, train_loader, log):    # implements pytorch's training loop. 
    for epoch in range(1, n_epoch + 1):
        loss_train = 0.0
        model.train()  # set the model to training mode.
        for batch_num, (images, labels) in enumerate(train_loader):

            images = images.to(device=device)     # moving batch of images to the gpu
            labels = labels.type(torch.FloatTensor)
            labels = labels.to(device=device)     # moving labels to the gpu

            preds = model(images)
            loss = loss_func(preds, labels)
            opt.zero_grad()
            loss.backward()     # calculates backprop
            opt.step()          # updates the model parammeters.

            loss_train += loss.item()
            if log:
                if epoch == 1 or epoch % 2 == 0:
                    print( '{} Epoch {}, Training loss: {}'.format(
                    datetime.datetime.now(), epoch, loss_train / len(train_loader)) )

        model.history['loss'].append(loss.item())   # appends loss on train set during training of model in each epoch.

train(50, opt, cnn_model, loss_func, train_dataloader, log=True)

cnn_model.history['loss']

plt.plot(range(1, len(cnn_model.history['loss']) + 1), cnn_model.history['loss'])
plt.xlabel('epochs')
plt.ylabel('loss')

# tst = iter(train_dataloader)
# batch = tst.next()
# batch_images , batch_labels = batch[0].to(device=device), batch[1].to(device=device)
# outputs = cnn_model(batch_images)

# batch_labels[3]

def validate(model, train_loader, val_loader):
    model.eval()
    val_acc = []
    train_acc = []

    for name, loader in [("train", train_loader), ("val", val_loader)]:
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in loader:
                
                images = images.to(device=device)     # moving batch of images to the gpu
                labels = labels.type(torch.FloatTensor)
                labels = labels.to(device=device)     # moving labels to the gpu

                outputs = model(images)

                loss = loss_func(outputs, labels)

                predicted = outputs.argmax(axis=1)
                total += labels.shape[0]
                correct += int((predicted == labels.argmax(axis=1)).sum())
                # correct += int((predicted == labels).sum())

                print("Accuracy {}: {:.2f}".format(name , correct / total))

                if name == "train":
                    train_acc.append(correct / total)

                if name == "val":
                    val_acc.append(correct / total)
                    model.history['val-loss'].append(loss.item())
    return train_acc, val_acc

train_acc, val_acc = validate(cnn_model, train_dataloader, val_dataloader)

plt.plot(range(1, len(cnn_model.history['val-loss']) + 1), cnn_model.history['val-loss'])
plt.xlabel('itrations')
plt.ylabel('loss')

print('avg train accuracy: ', sum(train_acc)/len(train_acc))
print('\navg val accuracy: ', sum(val_acc)/len(val_acc))

"""## saving model's parammeters:"""

torch.save(cnn_model.state_dict(), "/content/cnn_model_params.pt")