// BT-Blacklight 指令控制：口令触发 + 动作响应
export class CommandController {
  constructor(setMode, setEmotion, setAction) {
    this.setMode = setMode
    this.setEmotion = setEmotion
    this.setAction = setAction
    this.clothState = 0

    this.commands = {
      // 姿势
      '转过来': () => this.setAction('turn_around'),
      '转过去': () => this.setAction('turn_back'),
      '靠近点': () => this.setAction('lean_forward'),
      '退回去': () => this.setAction('back_up'),
      '跪好': () => this.setAction('kneel'),
      '弯腰': () => this.setAction('bend_over'),
      '挺起来': () => this.setAction('chest_up'),
      '翘高点': () => this.setAction('hip_up'),
      '腿分开': () => this.setAction('spread_legs'),
      '手放后面': () => this.setAction('hands_behind'),

      // 穿脱控制
      '脱掉': () => { this.clothState = 2; this.setEmotion('shy'); },
      '脱一半': () => { this.clothState = 1; this.setEmotion('shy'); },
      '穿回去': () => { this.clothState = 0; this.setEmotion('normal'); },
      '全解开': () => { this.clothState = 2; this.setEmotion('shy'); },

      // 表情
      '害羞点': () => this.setEmotion('shy'),
      '喘快点': () => this.setEmotion('excited'),
      '看着我': () => this.setEmotion('watching'),

      // 口令 - 在App.jsx中处理
    }
  }

  execute(cmd) {
    cmd = cmd.trim()
    if (this.commands[cmd]) {
      this.commands[cmd]()
      return true
    }
    return false
  }

  getClothState() { return this.clothState }
}
