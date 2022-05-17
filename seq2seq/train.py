from logging import handlers
import torch
import torch.nn as nn
import torch.optim as optim

import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

from load_data import train_iter, val_iter, id2vocab, PAD_IDX
from model import Encoder, Decoder, Seq2Seq, Attention

device = "cuda" if torch.cuda.is_available() else "cpu"

INPUT_DIM = len(id2vocab)
OUTPUT_DIM = len(id2vocab)
ENC_EMB_DIM = 256
DEC_EMB_DIM = 256
ENC_HID_DIM = 512
DEC_HID_DIM = 512
ENC_DROPOUT = 0.5
DEC_DROPOUT = 0.5
N_EPOCHS = 300
CLIP = 1

attn = Attention(ENC_HID_DIM, DEC_HID_DIM)
enc = Encoder(INPUT_DIM, ENC_EMB_DIM, ENC_HID_DIM, DEC_HID_DIM, ENC_DROPOUT)
dec = Decoder(OUTPUT_DIM, DEC_EMB_DIM, ENC_HID_DIM, DEC_HID_DIM, DEC_DROPOUT, attn)

model = Seq2Seq(enc, dec, device).to(device)

def init_weights(m):
    for name, param in m.named_parameters():
        if 'weight' in name:
            nn.init.normal_(param.data, mean=0, std=0.01)
        else:
            nn.init.constant_(param.data, 0)
model.apply(init_weights)

optimizer = optim.Adam(model.parameters(), lr=5e-5)
criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)

loss_vals = []
loss_vals_eval = []
for epoch in range(N_EPOCHS):
    model.train()
    epoch_loss = []
    pbar = tqdm(train_iter)
    pbar.set_description("[Train Epoch {}]".format(epoch))

    for trg, src in pbar:
        trg, src = trg.to(device), src.to(device)
        model.zero_grad()

        output = model(src, trg)
        output_dim = output.shape[-1]

        output = output[:, 1:, :].reshape(-1, output_dim)

        trg = trg[:, 1:].reshape(-1)

        loss = criterion(output, trg)
        loss.backward()

        torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP)
        epoch_loss.append(loss.item())
        optimizer.step()
        pbar.set_postfix(loss=loss.item())
    loss_vals.append(np.mean(epoch_loss))

    model.eval()
    epoch_loss_eval = []
    pbar = tqdm(val_iter)
    pbar.set_description("[Eval Epoch {}]".format(epoch))
    for trg, src in pbar:
        trg, src = trg.to(device), src.to(device)
        model.zero_grad()

        output = model(src, trg)

        output_dim = output.shape[-1]

        output = output[:, 1:, :].reshape(-1, output_dim)

        trg = trg[:, 1:].reshape(-1)

        loss = criterion(output, trg)
        epoch_loss_eval.append(loss.item())
        pbar.set_postfix(loss=loss.item())

    loss_vals_eval.append(np.mean(epoch_loss_eval))

torch.save(model.state_dict(), "model.pt")

l1 = plt.plot(np.linspace(1, N_EPOCHS, N_EPOCHS).astype(int), loss_vals)
l2 = plt.plot(np.linspace(1, N_EPOCHS, N_EPOCHS).astype(int), loss_vals_eval)
plt.legend(handlers=[l1, l2], labels=["Train loss", "Eval loss"], loc="best")



