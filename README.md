[![GitHub Actions][actions-shield]][actions]
[![GitHub Activity][commits-shield]][commits]
[![GitHub Last Commit][last-commit-shield]][commits]

![GitHub Stars][stars-shield]
![GitHub Watchers][watchers-shield]
![GitHub Forks][forks-shield]

# Slide API client

Python API client to utilise the Slide Cloud or local API.

## Usage


### Cloud API

```python
import asyncio
from slide import SlideCloud, get_slides

slide = SlideCloud(username="email@address.com", password="some-password")
slides = asyncio.run(get_slides(slide=slide))
print(f"Found slides: {','.join([s.device_name for s in slides])}")
```

### Local API

```python
import asyncio
from slide import SlideCloud, get_slide_state

slide = SlideCloud(base_url="http://192.168.1.10", device_code="some-device-code")
slide_state = asyncio.run(get_slide_state(slide=slide))
print(f"Got slide state: {slide_state}")
```

### Environment variables

Instead of providing explicit values for username/password or device code, you could also set environment variables. The used environment variables are listed and described below.

| Key                     | Description                                |
| ----------------------- | ------------------------------------------ |
| `SLIDE_API_USERNAME`    | Username when using the Slide Cloud API    |
| `SLIDE_API_PASSWORD`    | Password when using the Slide Cloud API    |
| `SLIDE_API_DEVICE_CODE` | Device code when using the local Slide API |

## Installation

```bash
pip install slide-api-client
```

[commits-shield]: https://img.shields.io/github/commit-activity/y/bartcode/slide-api-client.svg
[commits]: https://github.com/bartcode/slide-api-client/commits/main
[last-commit-shield]: https://img.shields.io/github/last-commit/bartcode/slide-api-client.svg
[stars-shield]: https://img.shields.io/github/stars/bartcode/slide-api-client.svg?style=social&label=Stars
[forks-shield]: https://img.shields.io/github/forks/bartcode/slide-api-client.svg?style=social&label=Forks
[watchers-shield]: https://img.shields.io/github/watchers/bartcode/slide-api-client.svg?style=social&label=Watchers
[actions-shield]: https://img.shields.io/github/actions/workflow/status/bartcode/slide-api-client/publish.yml
[actions]: https://github.com/bartcode/slide-api-client/actions
