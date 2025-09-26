import torch
import torch.nn as nn
import torchvision.models as models
from torchvision.models.resnet import resnet50

class Encoder(nn.Module):

    def __init__(self, embed_size = 512, train_CNN = False):
        super().__init__()
        self.cnn = models.densenet121(pretrained=False)
        self.train_CNN = train_CNN
        self.cnn.classifier = nn.Linear(in_features=self.cnn.classifier.in_features, out_features=embed_size)
        self.dropout = nn.Dropout(0.4)
        self.relu = nn.ReLU()

    
    def forward(self, x):
        x = self.cnn(x)
        x = self.relu(x)
        x = self.dropout(x)
        return x

        

class Decoder(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers = 1):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_size)
        self.lstm = nn.LSTM(embed_size, hidden_size, num_layers)
        self.linear = nn.Linear(hidden_size, vocab_size)
        self.dropout = nn.Dropout(0.5)
        
    
    def forward(self, x, captions):
        embeddings = self.dropout(self.embed(captions))
        embeddings = torch.cat((x.unsqueeze(0), embeddings), dim=0)
        hiddens, _ = self.lstm(embeddings)
        outputs = self.linear(hiddens)
        return outputs

class CNNtoRNN(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers):
        super(CNNtoRNN, self).__init__()
        self.encoderCNN = Encoder(embed_size)
        self.decoderRNN = Decoder(embed_size, hidden_size, vocab_size, num_layers)

    def forward(self, images, captions):
        features = self.encoderCNN(images)
        outputs = self.decoderRNN(features, captions)
        return outputs

    def caption_image(self, image, vocabulary, max_length=50):
        result_caption = []

        with torch.no_grad():
            x = self.encoderCNN(image).unsqueeze(0)
            states = None

            for _ in range(max_length):
                hiddens, states = self.decoderRNN.lstm(x, states)
                output = self.decoderRNN.linear(hiddens.squeeze(0))
                predicted = output.argmax(1)
                result_caption.append(predicted.item())
                x = self.decoderRNN.embed(predicted).unsqueeze(0)

                if vocabulary.itos[predicted.item()] == "<EOS>":
                    break

        return [vocabulary.itos[idx] for idx in result_caption]