import torch
import torch.nn as nn
from torch.autograd import Variable
import itertools, os, datetime
use_gpu = torch.cuda.is_available()

def validate_model(val_iter, model, criterion, TEXT, logger=None):
    model.eval()
  
    # Iterate over words in validation batch. 
    losses = AverageMeter()

loss_total = 0
  map_total = 0
  words_total = 0
  for i, batch in enumerate(val_iter):
    text = batch.text.cuda() if use_gpu else batch.text 
    targets = batch.target.cuda() if use_gpu else batch.target

    # Forward, calculate loss
    outputs, states = model(text, states)
    outputs = outputs.contiguous().view(outputs.size(0) * outputs.size(1), outputs.size(2))
    targets = targets.view(outputs.size(0)) # reshape for loss function

    # Remove '<eos>' from predictions
    outputs[TEXT.vocab.stoi['<eos>']] = -1000
    # outputs[TEXT.vocab.stoi['<unk>']] = -1000

    # Get top 20 predictions
    scores, preds = outputs.topk(20)
    rank_onehot = (preds == targets.view(-1,1)).data.float()
    map_scores = rank_onehot @ map_matrix
    map_total += map_scores.sum()
    words_total += len(map_scores)
    
    # Calculate losses
    loss = criterion(outputs, targets)
    loss_total += loss.data[0]
  
  # Log information after validation
  loss_avg = loss_total / len(val_iter) 
  map_avg = map_total / words_total
  ppl = torch.exp(torch.FloatTensor([loss_avg]))[0]
  info = 'Validation complete. MAP: {map:.3f}, \t Loss: {loss:.3f}, \t Sorta-Perplexity: {perplexity:.3f}'.format(
      map=map_avg, loss=loss_avg, perplexity=ppl)
  logger.log(info) if logger is not None else print(info)
  return ppl
