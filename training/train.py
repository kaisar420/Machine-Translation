import itertools, os, sys
sys.path.append('../')

import torch
import torch.nn as nn
from torch.autograd import Variable
use_gpu = torch.cuda.is_available()

from .valid import validate
from utils.utils import AverageMeter

def train(train_iter, val_iter, model, criterion, optimizer, scheduler, SRC, TRG, num_epochs, logger=None):  
    
    # Iterate through epochs
    bleu_best = -1
    for epoch in range(num_epochs):
    
        # Step learning rate scheduler
        scheduler.step()

        # Validate model
        bleu_val = validate_model(val_iter, model, criterion, SRC, TRG, logger)
        if bleu_val > bleu_best:
            bleu_best = bleu_val
            logger.save(model.state_dict())
            logger.log('New best: {}'.format(bleu_best))
    
        # Train model
        losses = AverageMeter()
        model.train()
        for i, batch in enumerate(train_iter): 
            src = batch.src.cuda() if use_gpu else batch.src
            trg = batch.trg.cuda() if use_gpu else batch.trg

            # Forward, backprop, optimizer
            model.zero_grad()
            scores = model(src, trg)
            scores = scores.view(scores.size(0) * scores.size(1), scores.size(2))
            trg = trg.view(scores.size(0))
            loss = criterion(scores, trg) 
            loss.backward()
            torch.nn.utils.clip_grad_norm(model.parameters(), 5.0)
            optimizer.step()

        # Log information
        if i % 1000 == 10:
            logger.log('''Epoch [{epochs}/{num_epochs}]
                       Batch [{batch}/{num_batches}]
                       Loss: {losses.avg:.3f}
                       '''.format(epochs=epoch+1, num_epochs=num_epochs, batch=i, num_batches=len(train_iter), losses=losses))
