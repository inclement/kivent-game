---VERTEX SHADER---
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* vertex attributes */
attribute vec2     vPosition;
attribute vec2     vTexCoords0;
attribute vec2     vCenter;
attribute float    vRotation;
attribute vec4     vColor;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;
uniform float      opacity;
uniform float      time;

void main (void) {
  /* frag_color = color * vec4(1.0, 1.0, 1.0,  */
  /*                           (1.0 - pow(1.0 - vColor.w, 3.0)) * opacity); */
  frag_color = vColor;
  tex_coord0 = vTexCoords0;
  float a_sin = sin(vRotation);
  float a_cos = cos(vRotation);
  mat4 rot_mat = mat4(a_cos, -a_sin, 0.0, 0.0,
                    a_sin, a_cos, 0.0, 0.0,
                    0.0, 0.0, 1.0, 0.0,
                    0.0, 0.0, 0.0, 1.0 );
  mat4 trans_mat = mat4(1.0, 0.0, 0.0, vCenter.x,
              0.0, 1.0, 0.0, vCenter.y,
              0.0, 0.0, 1.0, 0.0,
              0.0, 0.0, 0.0, 1.0);
  float xc = vPosition.x;
  float yc = vPosition.y;
  vec4 pos = vec4(vPosition.xy*.5, 0.0, 1.0) + 
    vec4(1.0 * sin(3.0*time+xc*yc), 1.0*cos(2.8*time+xc*yc), 0.0, 0.0);
  vec4 trans_pos = pos * rot_mat * trans_mat;
  gl_Position = projection_mat * modelview_mat * trans_pos;

}


---FRAGMENT SHADER---
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

void main (void){
  gl_FragColor = frag_color; 
}
