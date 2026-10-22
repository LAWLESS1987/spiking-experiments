"""Experiment 1: a small spiking neural network learns handwritten digits (MNIST).

What happens:
  - Each image is shown to the network for 25 time steps.
  - Neurons are leaky integrate-and-fire (LIF): each builds up charge, leaks a little every step, and fires a spike
    when it crosses a threshold, then resets. Information travels only as spikes (0 or 1), as in a neuromorphic chip.
  - The digit the network "says" is the output neuron that spikes most.

Run:  .venv\\Scripts\\python.exe exp1_mnist_snn.py
Out:  prints accuracy before and after training; saves exp1_spikes.png (a picture of the spikes).
Runs on the laptop's processor; no special hardware.
"""
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import snntorch as snn
from snntorch import surrogate
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

torch.manual_seed(0)
torch.set_num_threads(4)          # leave cores for the rest of the machine
STEPS, BETA, BATCH = 25, 0.9, 128
TRAIN_N, TEST_N = 12000, 2000     # a slice of MNIST so the first run takes a few minutes

tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0,), (1,))])
train = Subset(datasets.MNIST("data", train=True, download=True, transform=tf), range(TRAIN_N))
test = Subset(datasets.MNIST("data", train=False, download=True, transform=tf), range(TEST_N))
train_dl = DataLoader(train, batch_size=BATCH, shuffle=True)
test_dl = DataLoader(test, batch_size=BATCH)


class SNN(nn.Module):
    def __init__(self):
        super().__init__()
        grad = surrogate.fast_sigmoid()
        self.fc1, self.lif1 = nn.Linear(784, 300), snn.Leaky(beta=BETA, spike_grad=grad)
        self.fc2, self.lif2 = nn.Linear(300, 10), snn.Leaky(beta=BETA, spike_grad=grad)

    def forward(self, x):
        m1, m2 = self.lif1.init_leaky(), self.lif2.init_leaky()
        out_spikes, hidden_spikes = [], []
        x = x.flatten(1)
        for _ in range(STEPS):                 # the same image, presented over time
            s1, m1 = self.lif1(self.fc1(x), m1)
            s2, m2 = self.lif2(self.fc2(s1), m2)
            hidden_spikes.append(s1)
            out_spikes.append(s2)
        return torch.stack(out_spikes), torch.stack(hidden_spikes)


def accuracy(net):
    net.eval()
    right = total = 0
    with torch.no_grad():
        for x, y in test_dl:
            out, _ = net(x)
            right += (out.sum(0).argmax(1) == y).sum().item()
            total += y.numel()
    net.train()
    return right / total


net = SNN()
opt = torch.optim.Adam(net.parameters(), lr=5e-4)
loss_fn = nn.CrossEntropyLoss()
print(f"before training: {accuracy(net):.1%} correct on {TEST_N} test digits (chance is about 10%)")

t0 = time.time()
for epoch in range(2):
    for x, y in train_dl:
        out, _ = net(x)
        loss = loss_fn(out.sum(0), y)          # more spikes on the right neuron = lower loss
        opt.zero_grad()
        loss.backward()
        opt.step()
    print(f"after epoch {epoch + 1}: {accuracy(net):.1%} correct  ({time.time() - t0:.0f} s so far)")

# Picture: one test digit, the hidden neurons' spikes over time, and the output neurons' spike counts.
x, y = test[0]
with torch.no_grad():
    out, hid = net(x.unsqueeze(0))
fig, ax = plt.subplots(1, 3, figsize=(13, 4))
ax[0].imshow(x.squeeze(), cmap="gray"); ax[0].set_title(f"input digit (true label {y})"); ax[0].axis("off")
h = hid[:, 0, :100].numpy()
t_idx, n_idx = h.nonzero()
ax[1].scatter(t_idx, n_idx, s=4, c="black")
ax[1].set_title("spikes of 100 hidden neurons"); ax[1].set_xlabel("time step"); ax[1].set_ylabel("neuron")
counts = out[:, 0, :].sum(0).numpy()
ax[2].bar(range(10), counts, color=["tab:orange" if i == counts.argmax() else "tab:gray" for i in range(10)])
ax[2].set_title(f"output spikes per digit -> network says {int(counts.argmax())}"); ax[2].set_xticks(range(10))
plt.tight_layout()
plt.savefig("exp1_spikes.png", dpi=110)
print("saved exp1_spikes.png")
print(f"hidden-layer activity on that digit: {h.mean():.1%} of neuron-steps spiked (sparse activity is what makes neuromorphic chips efficient)")
