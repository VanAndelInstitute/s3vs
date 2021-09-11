import config from './config.js';

const parseQueryString = () => {
  let params = {};
  let search = window.location.search.slice(1);
  if (search) {
    let parts = search.split("&");

    parts.forEach(function (part) {
      let subparts = part.split("=");
      let key = subparts[0];
      let value = subparts[1];
      params[key] = value;
    });
  }
  return params;
}

(async function($) {
    let params = parseQueryString();
    let imageId = params["imageId"];
    var label = document.getElementById("label");
    label.src = `${config.iiifUri}/${imageId}/label.jpg`;
    let viewer = new $.Viewer({
      constrainDuringPan: true,
      id: 'root',
      navigatorPosition: 'BOTTOM_RIGHT',
      navigatorAutoFade: false,
      showNavigator: true,
      showNavigationControl: false,
      tileSources: [`${config.iiifUri}/${imageId}/info.json`],
      maxZoomPixelRatio: 1,
      visibilityRatio: 0.5,
    });
    
    let response = await fetch(
      `${config.iiifUri}/${imageId}/properties.json`,
      {
        headers: {
          'Accept': 'application/json'
        },
      });
      if (!response.ok) {
        let error = await response.text();
        var span = document.createElement('span');
        span.style.color = "black";
        span.style.fontSize = "x-large";
        span.appendChild(document.createTextNode(error));
        document.getElementById("root").appendChild(span); 
        return
      }
      let props = await response.json();
    
    let magnification;
    try {
      viewer.scalebar({
        pixelsPerMeter: (1 / (Number(props["aperio.MPP"]) * 0.000001)),
        xOffset: 5,
        yOffset: 10,
        stayInsideImage: true,
        color: 'rgb(150,150,150)',
        fontColor: 'rgb(100,100,100)',
        backgroundColor: 'rgba(255,255,255,0.5)',
        barThickness: 2,
        sizeAndTextRenderer: scalebarSizeAndTextRenderer
      });
      viewer.addHandler('zoom', (e) => {
        magnification = Number(viewer.viewport.viewportToImageZoom(e.zoom) * props["aperio.AppMag"]).toPrecision(3) + "X";
      });
      viewer.measurementTool({
        mpp: {
          x: Number(props["aperio.MPP"]),
          y: Number(props["aperio.MPP"]),
        },
        //onAdd: this.setting.addRulerCallback,
        //onDelete: this.setting.deleteRulerCallback,
      });
    } catch (ex) {
      console.log(ex.message);
    }
    
    function scalebarSizeAndTextRenderer(ppm, minSize) {
      let getSizeAndText = OpenSeadragon.ScalebarSizeAndTextRenderer.METRIC_LENGTH;
      let {size, text} = getSizeAndText(ppm, minSize);
      return {
        size,
        text: text + " (" + magnification + ")"
      };
    }
  })(OpenSeadragon);