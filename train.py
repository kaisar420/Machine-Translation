import torch
import torch.nn as nn
from torch.autograd import Variable
import itertools, os, datetime
use_gpu = torch.cuda.is_available()

from valid import validate_model

def detach(states):
  '''Helpful function for backprop'''
  return tuple(state.detach() for state in states)

def train_model(train_iter, val_iter, model, criterion, max_norm=1.0, num_epochs=2, logger=None):  
  model.train()
  for epoch in range(num_epochs):
    
    # Initial states for LSTM
    batch_size = train_iter.batch_size
    num_layers, hidden_size = model.num_layers, model.hidden_size
    init = Variable(torch.zeros(num_layers, batch_size, hidden_size))
    init = init.cuda() if use_gpu else init
    states = (init, init.clone())

    # Validate model
    best_losses = 0
    val_losses = validate_model(val_iter, model, criterion, logger)
    if val_losses < best_losses:
      # torch.save(model.state_dict(), 'model-{}.pkl'.format(datetime.datetime.now().strftime("%m-%d-%H-%M-%S")))
      best_losses = val_losses 
    
    # Train model
    losses = 0
    for i, batch in enumerate(train_iter): 
      text = batch.text.cuda() if use_gpu else batch.text
      targets = batch.target.cuda() if use_gpu else batch.target

      # Forward, backprop, optimizer
      model.zero_grad()
      states = detach(states)
      outputs, states = model(text, states)
      outputs = outputs.view(outputs.size(0) * outputs.size(1), outputs.size(2))
      targets = targets.view(outputs.size(0))
      loss = criterion(outputs, targets) 
      loss.backward()
      torch.nn.utils.clip_grad_norm(model.parameters(), max_norm)
      optimizer.step()
      
      # Log information
      losses += loss.data[0]
      log_freq = 1000
      if i % log_freq == 10:
        losses_for_log = losses / (i * train_iter.batch_size)
        info = 'Epoch [{epochs}/{num_epochs}], Batch [{batch}/{num_batches}], Loss: {loss:.3f}, Sorta-Perplexity: {perplexity:.3f}'.format(
            epochs=epoch+1, num_epochs=num_epochs, batch=i, num_batches=len(train_iter), loss=losses_for_log, perplexity=torch.exp(torch.FloatTensor([losses_for_log]))[0])
        logger.log(info) if logger is not None else print(info)
        torch.save(model.state_dict(), 'saves/model.pkl')
