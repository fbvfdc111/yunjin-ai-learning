from __future__ import annotations


def build_resnet18(num_outputs: int, pretrained: bool = True):
    try:
        from torch import nn
        from torchvision.models import ResNet18_Weights, resnet18
    except ImportError as exc:
        raise RuntimeError("Install requirements before constructing a model") from exc
    weights = ResNet18_Weights.DEFAULT if pretrained else None
    model = resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_outputs)
    return model


def default_transforms(train: bool, image_size: int = 224):
    try:
        from torchvision import transforms
    except ImportError as exc:
        raise RuntimeError("Install requirements before constructing transforms") from exc
    if train:
        return transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(brightness=0.1, contrast=0.1),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

